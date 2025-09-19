"""
logic.py
========
Processing, validation, sanitization, and import orchestration for datasheets.

Purpose
-------
This module sits between `core.datasheet_importer` (which extracts raw tables
from files) and `db.database.save_dataframe` (which persists DataFrames to SQLite).
It provides:
- a safe preview/analyze flow (no DB writes)
- a full pipeline that can auto-fix, validate, and optionally write to DB
- detailed reports suitable for GUI presentation or logging
- helpers for schema mapping (generic -> inventory schema)

Design Principles
-----------------
- Non-destructive by default: previews and analyses do not modify the database.
- Explainable: all coercions, errors, and fixes are returned in structured reports.
- Conservative auto-fixes: we try to coerce when safe but never silently drop data unless explicitly requested.
- Extensible: mapping heuristics and validation rules are centralized to allow easy updates.

Usage examples
--------------
>>> from core import logic
>>> report = logic.preview_and_analyze("specs.xlsx")
>>> # present report to user in UI, then:
>>> commit_report = logic.process_and_import("specs.xlsx", db_path="db/inventory.db",
...                                         prefer_table_name="warehouse_1",
...                                         dry_run=False, auto_fix=True)

Dependencies
------------
- pandas
- numpy
- core.datasheet_importer (local module provided by project)
- db.database.save_dataframe (local DB writer; uses SQLAlchemy under the hood)

Notes / Caveats
---------------
- For very large CSVs (>100k rows) this module loads full DataFrames into memory.
  Consider adding streaming/chunked ingestion for production-scale datasets.
- OCR-based image parsing accuracy depends on image quality and tesseract configuration.
- Column name mapping uses heuristics; for business-critical imports, allow users to
  confirm or set mappings manually in the UI.
"""

from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
import re
import logging

import pandas as pd
import numpy as np

from core import datasheet_importer
from db.database import save_dataframe  # uses SQLAlchemy engine under the hood

# ------------------------------------------------------------
# Logging configuration (local logger; application may reconfigure)
# ------------------------------------------------------------
logger = logging.getLogger("inventory.logic")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


# ------------------------------------------------------------
# Constants and heuristics
# ------------------------------------------------------------

# Inventory "roles" and candidate column names (lowercase). Expand as needed.
INVENTORY_KEYS: Dict[str, Dict[str, List[str]]] = {
    "name": {"candidates": ["name", "product", "item", "description", "title"]},
    "quantity": {"candidates": ["quantity", "qty", "stock", "count", "amount"]},
    "price": {"candidates": ["price", "cost", "amount", "rate", "unit_price", "mrp"]},
    "id": {"candidates": ["id", "item_id", "product_id", "sku"]},
}

# Default behavior for numerical tolerance when coercing floats to ints
INT_COERCE_EPSILON = 1e-6


# ------------------------------------------------------------
# Helper utilities
# ------------------------------------------------------------

def _slug(s: str) -> str:
    """
    Return a safe slug suitable for SQLite table names using datasheet_importer.slugify.

    Parameters
    ----------
    s : str
        Any string (file name, sheet name, custom table name).

    Returns
    -------
    str
        Sanitized slug (lowercase, underscores, alphanumeric).
    """
    return datasheet_importer.slugify(s)


def _strip_text(x: Any) -> Any:
    """
    Trim whitespace from string-like values, leave NaNs alone.

    Returns the original type whenever possible (i.e., don't force strings on numbers).

    Parameters
    ----------
    x : Any
        Value to strip.

    Returns
    -------
    Any
        Stripped string or original non-string value.
    """
    if pd.isna(x):
        return x
    try:
        return str(x).strip()
    except Exception:
        return x


def _parse_number_like(val: Any) -> Tuple[Any, str]:
    """
    Attempt to coerce a value that looks like a number into a float.

    Heuristics:
    - Removes currency symbols and letters
    - Handles thousands separators (commas) and decimal comma fallback
    - Converts parentheses '(123)' -> -123

    Returns
    -------
    (parsed_value, status)
        parsed_value : float or the original value if parse failed or NaN for empty
        status : 'ok' (already numeric), 'coerced' (string -> float),
                 'na' (empty/NaN), 'fail' (couldn't parse)
    """
    if pd.isna(val):
        return (np.nan, "na")
    if isinstance(val, (int, float, np.integer, np.floating)):
        return (float(val), "ok")
    s = str(val).strip()
    if s == "":
        return (np.nan, "na")
    # Remove anything except digits, dot, comma, minus, parentheses
    s2 = re.sub(r"[^\d\.\-\,\(\)]", "", s)
    if not s2:
        return (val, "fail")
    # Parentheses indicate negative number e.g. "(1,234.00)"
    if s2.startswith("(") and s2.endswith(")"):
        s2 = "-" + s2[1:-1]
    # Thousands separators heuristics:
    # - if more than 1 comma, assume commas are thousands separators -> drop them
    if s2.count(",") > 1:
        s2 = s2.replace(",", "")
    # - if there are commas and no dot, interpret comma as decimal separator
    if "," in s2 and "." not in s2:
        s2 = s2.replace(",", ".")
    try:
        v = float(s2)
        return (v, "coerced")
    except Exception:
        return (val, "fail")


# ------------------------------------------------------------
# Mapping / inference
# ------------------------------------------------------------

def guess_column_for(role: str, cols: List[str]) -> Optional[str]:
    """
    Choose the most-likely column name to fulfill a role (e.g., 'price', 'quantity').

    Strategy:
    - Exact name match against preferred candidates
    - Substring fuzzy match (candidate contained in column name)
    - Returns first match found in original column order to favor leftmost columns.

    Parameters
    ----------
    role : str
        One of the keys in INVENTORY_KEYS (id, name, quantity, price).
    cols : List[str]
        List of DataFrame column names.

    Returns
    -------
    Optional[str]
        The original column name from `cols` that best matches the role, or None.
    """
    candidates = INVENTORY_KEYS.get(role, {}).get("candidates", [])
    cols_lower = {c.lower(): c for c in cols}

    # Priority 1: exact candidate match
    for cand in candidates:
        if cand in cols_lower:
            return cols_lower[cand]

    # Priority 2: substring match in any column name
    for cand in candidates:
        for c_lower, orig in cols_lower.items():
            if cand in c_lower:
                return orig

    return None


def map_to_inventory_df(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Try to map a generic DataFrame to the inventory schema with columns:
    ['id', 'name', 'quantity', 'price'].

    Preserves any extra columns by prefixing them with 'meta_' and slugifying the
    column name so we don't lose information.

    Parameters
    ----------
    df : pd.DataFrame
        Input table to map.

    Returns
    -------
    mapped : pd.DataFrame
        DataFrame containing columns (some combination of id, name, quantity, price, meta_*).
    mapping_report : dict
        Detailed mapping decisions and notes for GUI display.

    Example
    -------
    >>> mapped, report = map_to_inventory_df(raw_df)
    """
    report: Dict[str, Any] = {"mapping": {}, "notes": []}
    cols = list(df.columns)
    mapped = pd.DataFrame(index=df.index)  # keep index alignment initially

    # Map core roles
    for role in ("id", "name", "quantity", "price"):
        found = guess_column_for(role, cols)
        report["mapping"][role] = found
        if found:
            mapped[role] = df[found]
        else:
            mapped[role] = pd.NA  # placeholder column to maintain predictable schema
            if role == "name":
                report["notes"].append("No candidate found for 'name'; placeholders may be generated.")
            elif role in ("quantity", "price"):
                report["notes"].append(f"No candidate found for '{role}'; values will be missing (NaN) by default.")

    # Preserve other columns as meta_*
    for c in cols:
        if c not in report["mapping"].values():
            meta_col = f"meta_{_slug(c)}"
            # Avoid collision with existing names
            if meta_col in mapped.columns:
                i = 1
                while f"{meta_col}_{i}" in mapped.columns:
                    i += 1
                meta_col = f"{meta_col}_{i}"
            mapped[meta_col] = df[c]

    # Reset index to sequential integers for downstream consumers
    mapped = mapped.reset_index(drop=True)
    return mapped, report


# ------------------------------------------------------------
# Sanitization, validation, auto-fixes
# ------------------------------------------------------------

def sanitize_dataframe(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Clean string columns and attempt numeric normalization for quantity/price.

    Actions performed:
    - Strip whitespace on object dtype columns
    - Try to parse 'quantity' and 'price' with _parse_number_like
    - Return logs describing coercions and parse failures

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    (sanitized_df, logs)
        sanitized_df : pd.DataFrame (copy)
        logs : list[str] messages describing what was done
    """
    logs: List[str] = []
    df = df.copy()

    # Strip text columns
    for c in df.select_dtypes(include=["object"]).columns:
        before_nonnull = int(df[c].notna().sum())
        df[c] = df[c].map(_strip_text)
        after_nonnull = int(df[c].notna().sum())
        if before_nonnull != after_nonnull:
            logs.append(f"Stripped column '{c}': non-null {before_nonnull} -> {after_nonnull}")

    # Attempt numeric parsing for expected numeric columns
    for col in ("quantity", "price"):
        if col in df.columns:
            statuses = {"ok": 0, "coerced": 0, "na": 0, "fail": 0}
            parsed_values = []
            example_fails: List[str] = []
            for val in df[col]:
                parsed_val, status = _parse_number_like(val)
                parsed_values.append(parsed_val)
                statuses[status] = statuses.get(status, 0) + 1
                if status == "fail" and len(example_fails) < 5:
                    example_fails.append(str(val))
            df[col] = parsed_values
            logs.append(f"Column '{col}' parse summary: {statuses}")
            if example_fails:
                logs.append(f"Column '{col}' parse failures (examples): {example_fails}")
    return df, logs


def validate_inventory_df(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate an inventory-style DataFrame.

    Rules checked:
    - 'name' presence and missing count
    - 'quantity' integer-likeness and non-negativity
    - 'price' numeric-likeness and non-negativity

    Returns
    -------
    dict
        {
            'errors': [str, ...],
            'warnings': [str, ...],
            'stats': {'rows': int}
        }

    Notes
    -----
    This function is conservative: it flags issues but does not mutate the DataFrame.
    For automated corrections, use `auto_fix_inventory_df`.
    """
    errors: List[str] = []
    warnings: List[str] = []
    stats = {"rows": len(df)}

    # Name checks
    if "name" not in df.columns:
        warnings.append("Missing 'name' column.")
    else:
        n_missing = int(df["name"].isna().sum())
        if n_missing:
            warnings.append(f"{n_missing} rows missing 'name'")

    # Quantity checks
    if "quantity" in df.columns:
        def is_integer_like(x: Any) -> bool:
            try:
                if pd.isna(x):
                    return False
                if isinstance(x, (int, np.integer)):
                    return True
                if isinstance(x, float):
                    return abs(x - round(x)) < INT_COERCE_EPSILON
                s = str(x).strip()
                return bool(re.match(r"^-?\d+$", s))
            except Exception:
                return False

        bad_q = df["quantity"].apply(lambda x: not (pd.isna(x) or is_integer_like(x)))
        if bad_q.any():
            errors.append(f"{int(bad_q.sum())} rows have non-integer-like 'quantity' values.")
        try:
            negative_q = int(df["quantity"].apply(lambda x: float(x) < 0 if pd.notna(x) else False).sum())
            if negative_q:
                errors.append(f"{negative_q} rows have negative 'quantity' values.")
        except Exception:
            errors.append("Could not evaluate numeric values for 'quantity' to check negativity.")

    else:
        warnings.append("No 'quantity' column present; default behavior will set quantity=0 if auto-fixed.")

    # Price checks
    if "price" in df.columns:
        bad_price_count = int(df["price"].apply(lambda x: False if pd.isna(x) else not isinstance(x, (int, float, np.integer, np.floating))).sum())
        if bad_price_count:
            errors.append(f"{bad_price_count} rows have non-numeric 'price' values.")
        try:
            negative_price = int(df["price"].apply(lambda x: float(x) < 0 if pd.notna(x) else False).sum())
            if negative_price:
                errors.append(f"{negative_price} rows have negative 'price' values.")
        except Exception:
            errors.append("Could not evaluate numeric values for 'price' to check negativity.")
    else:
        warnings.append("No 'price' column present; default behavior will set price=0.0 if auto-fixed.")

    return {"errors": errors, "warnings": warnings, "stats": stats}


def auto_fix_inventory_df(df: pd.DataFrame, remove_bad_rows: bool = False) -> Tuple[pd.DataFrame, List[str]]:
    """
    Attempt to fix common import problems.

    Fixes applied:
    - Generate 'name' placeholders for missing names (item_1, item_2, ...)
    - Coerce quantity floats close to integers into ints
    - Coerce numeric strings into float for price and int for quantity when possible
    - Insert default columns quantity=0 and price=0.0 if missing
    - Optionally remove rows with irrecoverable problems (controlled by remove_bad_rows)

    Parameters
    ----------
    df : pd.DataFrame
    remove_bad_rows : bool, default False
        If True, drop rows that are still invalid after coercion.

    Returns
    -------
    (cleaned_df, actions)
        cleaned_df : pd.DataFrame
        actions : list[str] messages describing what was changed
    """
    actions: List[str] = []
    df = df.copy()

    # Ensure name exists
    if "name" not in df.columns:
        df["name"] = [f"item_{i+1}" for i in range(len(df))]
        actions.append("Created 'name' column with placeholders for all rows.")
    else:
        missing_mask = df["name"].isna() | (df["name"].astype(str).str.strip() == "")
        if missing_mask.any():
            for i in df[missing_mask].index:
                df.at[i, "name"] = f"item_{i+1}"
            actions.append(f"Filled {int(missing_mask.sum())} missing 'name' values with placeholders.")

    # Quantity coercion
    if "quantity" in df.columns:
        def coerce_qty(x: Any) -> Any:
            if pd.isna(x):
                return np.nan
            if isinstance(x, (int, np.integer)):
                return int(x)
            try:
                f = float(x)
                # if float within epsilon of integer, convert to int
                if abs(f - round(f)) < INT_COERCE_EPSILON:
                    return int(round(f))
                return int(round(f))  # fallback: round floats to nearest int
            except Exception:
                return x

        before_na = int(df["quantity"].isna().sum())
        df["quantity"] = df["quantity"].apply(coerce_qty)
        after_na = int(pd.isna(df["quantity"]).sum())
        actions.append(f"Coerced 'quantity' values; NaNs {before_na} -> {after_na}.")
    else:
        # if quantity missing entirely, introduce default zeros
        df["quantity"] = 0
        actions.append("Inserted 'quantity' column with default 0 for all rows.")

    # Price coercion
    if "price" in df.columns:
        def coerce_price(x: Any) -> Any:
            if pd.isna(x):
                return np.nan
            if isinstance(x, (int, float, np.integer, np.floating)):
                return round(float(x), 2)
            try:
                return round(float(x), 2)
            except Exception:
                return x

        df["price"] = df["price"].apply(coerce_price)
        actions.append("Attempted to coerce 'price' to float and rounded to 2 decimals where possible.")
    else:
        df["price"] = 0.0
        actions.append("Inserted 'price' column with default 0.0 for all rows.")

    # Optionally drop irrecoverable rows
    if remove_bad_rows:
        before = len(df)
        def is_good_row(row: pd.Series) -> bool:
            try:
                if pd.isna(row.get("name")) or str(row.get("name")).strip() == "":
                    return False
                if pd.isna(row.get("quantity")):
                    return False
                if pd.isna(row.get("price")):
                    return False
                return True
            except Exception:
                return False
        df = df[df.apply(is_good_row, axis=1)].reset_index(drop=True)
        actions.append(f"Removed {before - len(df)} rows with irrecoverable problems via remove_bad_rows=True.")

    return df.reset_index(drop=True), actions


# ------------------------------------------------------------
# Orchestration: preview + commit flows
# ------------------------------------------------------------

def preview_and_analyze(path: str) -> List[Dict[str, Any]]:
    """
    Ingest a datasheet and produce a non-destructive analysis report for each detected table.

    Steps:
    - Uses core.datasheet_importer.ingest_file to parse file into DataFrames
    - Attempts mapping into inventory schema with `map_to_inventory_df`
    - Sanitizes each mapped DataFrame
    - Runs validation to produce errors/warnings/stats

    Parameters
    ----------
    path : str
        Path to the input file. Supported extensions handled by datasheet_importer.

    Returns
    -------
    List[dict]
        List of table reports with the following keys:
        - file_table_name: original logical name (sheet name / file stem)
        - mapped_table_name: slugified name suitable for DB tables
        - original_df: original DataFrame (as returned by parser)
        - mapped_df: DataFrame after mapping role columns (not sanitized)
        - sanitized_df: DataFrame after basic sanitization (not auto-fixed)
        - sanitize_logs: list[str] messages
        - validation: result of validate_inventory_df(mapped/sanitized)
        - mapping_report: mapping details and notes

    Raises
    ------
    FileNotFoundError
        If `path` does not exist (delegated to datasheet_importer)
    ValueError
        If file extension unsupported (delegated to datasheet_importer)
    """
    parsed = datasheet_importer.ingest_file(path)
    results: List[Dict[str, Any]] = []

    for raw_name, df in parsed:
        mapped_df, mapping_report = map_to_inventory_df(df)
        sanitized_df, sanitize_logs = sanitize_dataframe(mapped_df)
        validation = validate_inventory_df(sanitized_df)
        results.append({
            "file_table_name": raw_name,
            "mapped_table_name": _slug(raw_name),
            "original_df": df,
            "mapped_df": mapped_df,
            "sanitized_df": sanitized_df,
            "sanitize_logs": sanitize_logs,
            "validation": validation,
            "mapping_report": mapping_report,
        })

    return results


def process_and_import(path: str,
                       db_path: str,
                       prefer_table_name: Optional[str] = None,
                       dry_run: bool = True,
                       auto_fix: bool = True,
                       remove_bad_rows: bool = False,
                       if_exists: str = "append") -> Dict[str, Any]:
    """
    Full import pipeline: analyze, optionally auto-fix, and optionally persist.

    Parameters
    ----------
    path : str
        Path to the datasheet file.
    db_path : str
        SQLite database file path to write into.
    prefer_table_name : Optional[str]
        If provided, this name (slugified) will be used as target DB table name for every
        parsed table. If None, uses slugified file_table_name provided by parser.
    dry_run : bool, default True
        If True, do not write to DB; still return the full report.
    auto_fix : bool, default True
        If True, run `auto_fix_inventory_df` before writing/validating final state.
    remove_bad_rows : bool, default False
        If True (and auto_fix True), drop irrecoverable rows.
    if_exists : str, default "append"
        Passed to save_dataframe: "fail", "replace", or "append".

    Returns
    -------
    dict
        {
            'file': path,
            'tables': [
                {
                    'file_table_name': str,
                    'mapped_table_name': str,
                    'mapping_report': {...},
                    'sanitize_logs': [...],
                    'validation_before': {...},
                    'actions': [...],
                    'validation_after': {...},
                    'rows_written': int,
                    'errors': [...]
                }, ...
            ]
        }

    Behavior
    --------
    - The function is safe by default (dry_run). Call with dry_run=False to commit.
    - All exceptions during DB writes are captured and returned in the per-table 'errors' list.
    """
    previews = preview_and_analyze(path)
    report: Dict[str, Any] = {"file": path, "tables": []}

    for item in previews:
        table_report: Dict[str, Any] = {
            "file_table_name": item["file_table_name"],
            "mapped_table_name": item["mapped_table_name"],
            "mapping_report": item["mapping_report"],
            "sanitize_logs": item["sanitize_logs"],
            "validation_before": item["validation"],
            "actions": [],
            "rows_written": 0,
            "errors": []
        }

        df = item["sanitized_df"]

        if auto_fix:
            df, actions = auto_fix_inventory_df(df, remove_bad_rows=remove_bad_rows)
            table_report["actions"].extend(actions)
            table_report["validation_after"] = validate_inventory_df(df)
        else:
            table_report["validation_after"] = item["validation"]

        # Determine output table name
        out_table_name = _slug(prefer_table_name) if prefer_table_name else item["mapped_table_name"]

        try:
            if not dry_run:
                save_dataframe(df, out_table_name, db_path=db_path, if_exists=if_exists)
                table_report["rows_written"] = len(df)
                logger.info(f"Wrote {len(df)} rows to {db_path} :: {out_table_name} (if_exists={if_exists})")
            else:
                # dry-run: no writes
                table_report["rows_written"] = 0
                logger.info(f"Dry run: would write {len(df)} rows to {out_table_name}")
        except Exception as exc:
            # Capture exception details in report but do not raise so caller can present to user
            logger.exception("Failed to write table to DB")
            table_report["errors"].append(str(exc))

        report["tables"].append(table_report)

    return report


# ------------------------------------------------------------
# Small CLI helper for debugging from terminal (keeps file importable)
# ------------------------------------------------------------
def _print_report(report: Dict[str, Any]) -> None:
    """
    Nicely print the report returned by process_and_import for debugging.
    Intended for developer use (CLI or quick tests).
    """
    print(f"File: {report.get('file')}")
    for t in report.get("tables", []):
        print("-" * 60)
        print(f"Table (file): {t.get('file_table_name')} -> DB name: {t.get('mapped_table_name')}")
        print("Mapping:", t.get("mapping_report", {}).get("mapping"))
        notes = t.get("mapping_report", {}).get("notes", [])
        if notes:
            print("Notes:", notes)
        print("Sanitize logs:")
        for l in t.get("sanitize_logs", [])[:6]:
            print("  ", l)
        print("Validation before:", t.get("validation_before"))
        if "validation_after" in t:
            print("Validation after:", t.get("validation_after"))
        if t.get("actions"):
            print("Actions:", t.get("actions"))
        print("Rows written:", t.get("rows_written"))
        if t.get("errors"):
            print("Errors:", t.get("errors"))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Preview and optionally import datasheet into inventory DB.")
    parser.add_argument("file", help="Path to datasheet file")
    parser.add_argument("--db", help="Path to sqlite db", required=True)
    parser.add_argument("--table", help="Preferred table name (optional)", default=None)
    parser.add_argument("--commit", action="store_true", help="Actually write to DB (default is dry-run)")
    parser.add_argument("--no-auto-fix", action="store_true", help="Disable automatic fixes")
    parser.add_argument("--remove-bad", action="store_true", help="Remove irrecoverable rows when auto-fixing")
    parser.add_argument("--if-exists", choices=("fail", "replace", "append"), default="append", help="How to handle existing table")
    args = parser.parse_args()

    rep = process_and_import(
        args.file,
        db_path=args.db,
        prefer_table_name=args.table,
        dry_run=not args.commit,
        auto_fix=not args.no_auto_fix,
        remove_bad_rows=args.remove_bad,
        if_exists=args.if_exists
    )
    _print_report(rep)

"""
datasheet_importer.py
---------------------

This module is responsible for ingesting external datasheet files
(CSV, Excel, PDF, TXT, and even images with OCR) and turning them
into clean Pandas DataFrames that can later be saved into the project database.

Usage example (non-GUI):
    from core import datasheet_importer
    tables = datasheet_importer.ingest_file("spec_sheet.xlsx")
    for name, df in tables:
        print("Table:", name)
        print(df.head())

Design notes:
- The importer never writes directly to the database.
- It only extracts and normalizes tabular data → returns (table_name, DataFrame).
- Database integration happens in `db/database.py`.
- GUI integration (button click → file select → import) happens in `ui/gui.py`.

Supported formats:
- CSV / TSV
- Excel (.xls, .xlsx)
- TXT (tab/comma/whitespace separated, or fallback to raw lines)
- PDF (uses pdfplumber to detect tables)
- Images (uses pytesseract OCR to detect text and heuristics for tables)
"""

import re
from pathlib import Path
import pandas as pd
import pdfplumber
from PIL import Image
import pytesseract

# ----------------------------------------------------------------------
# Utility helpers
# ----------------------------------------------------------------------


def slugify(name: str) -> str:
    """
    Turn an arbitrary string into a safe SQLite table name.

    Examples:
        "Product Specs 2025!" → "product_specs_2025"
        "Voltage (V)"         → "voltage_v"

    Limits:
        - Lowercases everything
        - Replaces whitespace with underscores
        - Removes non-alphanumeric characters
        - Defaults to "table" if name is empty
    """
    name = name.strip().lower()
    name = re.sub(r"\s+", "_", name)  # collapse spaces → "_"
    name = re.sub(r"[^\w\d_]", "", name)  # strip symbols
    return name or "table"


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize column names of a DataFrame so they are safe to use in SQLite.

    - Applies `slugify` to each column name
    - If a column has no name, generates col_1, col_2, etc.

    Parameters:
        df (pd.DataFrame): Original dataframe

    Returns:
        pd.DataFrame: New dataframe with cleaned column names
    """
    df = df.copy()
    df.columns = [
        slugify(str(c)) or f"col_{i}" for i, c in enumerate(df.columns, start=1)
    ]
    return df


# ----------------------------------------------------------------------
# Parsers for different file formats
# ----------------------------------------------------------------------


def parse_csv(path: Path):
    """Parse a CSV or TSV file into a single DataFrame."""
    df = pd.read_csv(path, low_memory=False)
    return [(path.stem, normalize_columns(df))]


def parse_excel(path: Path):
    """Parse an Excel file (all sheets) into multiple DataFrames."""
    xls = pd.ExcelFile(path)
    return [
        (f"{path.stem}_{sheet}", normalize_columns(xls.parse(sheet)))
        for sheet in xls.sheet_names
    ]


def parse_txt(path: Path):
    """
    Parse a plain-text file into a DataFrame.

    Heuristics:
        - If tabs are present → treat as TSV
        - If commas dominate → treat as CSV
        - Else fallback: each line is one row in a 'text' column
    """
    text = path.read_text(encoding="utf-8", errors="ignore")
    if "\t" in text:
        df = pd.read_csv(path, sep="\t", engine="python")
    elif text.count(",") > text.count("\n"):
        df = pd.read_csv(path, sep=",", engine="python")
    else:
        df = pd.DataFrame({"text": text.splitlines()})
    return [(path.stem, normalize_columns(df))]


def parse_pdf(path: Path):
    """
    Parse a PDF file and extract tables using pdfplumber.

    For each page:
        - Detects tables → converts them into DataFrames
        - Normalizes column names
        - Tables are named like file_p1_t0 (page 1, table 0)

    Limitations:
        - Complex layouts may not be detected properly
        - If no tables are found, consider switching to Camelot/Tabula
    """
    tables = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            for j, tbl in enumerate(page.extract_tables()):
                df = pd.DataFrame(tbl[1:], columns=tbl[0]
                                  )  # first row → header
                tables.append(
                    (f"{path.stem}_p{i}_t{j}", normalize_columns(df)))
    return tables


def parse_image(path: Path):
    """
    Parse an image of a datasheet using OCR (Tesseract).

    Workflow:
        - Run OCR to extract text
        - Split text into lines
        - Replace multiple spaces with tabs (heuristic → simulate columns)
        - Try to parse as tab-separated file
        - Fallback: one column 'text' with raw lines

    Note:
        - Accuracy depends heavily on image quality and OCR training
    """
    img = Image.open(path)
    text = pytesseract.image_to_string(img)
    lines = [re.sub(r"\s{2,}", "\t", l.strip())
             for l in text.splitlines() if l.strip()]
    if not lines:
        return []
    try:
        df = pd.read_csv(
            pd.compat.StringIO("\n".join(lines)), sep="\t", engine="python"
        )
    except Exception:
        df = pd.DataFrame({"text": lines})
    return [(path.stem, normalize_columns(df))]


# ----------------------------------------------------------------------
# Dispatcher
# ----------------------------------------------------------------------

PARSERS = {
    ".csv": parse_csv,
    ".tsv": parse_csv,
    ".xls": parse_excel,
    ".xlsx": parse_excel,
    ".txt": parse_txt,
    ".pdf": parse_pdf,
    ".png": parse_image,
    ".jpg": parse_image,
    ".jpeg": parse_image,
}


def ingest_file(path: str):
    """
    Ingest a file into normalized DataFrames.

    Parameters:
        path (str): Path to file (CSV, Excel, PDF, TXT, or image)

    Returns:
        list of (table_name, DataFrame) tuples
            e.g. [("spec_sheet", DataFrame), ("spec_sheet_sheet2", DataFrame)]

    Raises:
        FileNotFoundError if path does not exist
        ValueError if file extension is unsupported
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)
    ext = p.suffix.lower()
    parser = PARSERS.get(ext)
    if not parser:
        raise ValueError(f"Unsupported file type: {ext}")
    return parser(p)

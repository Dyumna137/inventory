# GUI Developer Guide — Offline Inventory Management

This short guide explains how the Tkinter GUI ties into the rest of the
project, how to extend or reuse the patterns in other languages, and gives
sample flows you can copy into future projects.

---

## 1) Architecture overview

Components:
- `gui.py` (documented here as `gui_documented.py`): User interface (Tkinter)
- `core/datasheet_importer.py`: Parses input files into Pandas DataFrames
- `core/logic.py`: (Optional) Validation, mapping, sanitization, preview + import orchestration
- `db/database.py`: Persistence layer (sqlite3 + SQLAlchemy helper for DataFrames)

Integration points:
- GUI uses `database.get_table_names`, `get_column_names`, and `fetch_table_rows` to inspect and display current DB state.
- GUI calls `database.insert_item`, `update_item`, `delete_item` for CRUD on inventory schema.
- For datasheet import, GUI calls `datasheet_importer.ingest_file` to get DataFrames, then persists via `save_dataframe`.
- For a safer import UX, call `core.logic.preview_and_analyze` from the GUI to show a preview+validation step before calling `process_and_import(commit=True)`.

---

## 2) Recommended GUI flow for safer imports

1. User clicks "Import Datasheet" → present file picker
2. Call `core.logic.preview_and_analyze(path)` → this returns parsed tables with mapping, sanitize logs, and validation
3. Open a modal presenting the preview for each table (first 10 rows), mapping suggestions, and warnings/errors
4. Let user (a) rename the target table, (b) choose whether to auto-fix, (c) choose `if_exists` behavior
5. If user confirms, call `core.logic.process_and_import(path, db_path, prefer_table_name=..., dry_run=False)`
6. Show final report and refresh table dropdown/listbox

Why this flow? It prevents accidental schema mistakes and gives the user a chance to rename/clean up imported tables.

---

## 3) Developer checklist for integrating similar GUI in other languages

These patterns are language-agnostic. Replace the specific APIs but keep the structure:

1. **Clear separation of concerns**:
   - UI only handles input, presentation, and orchestration.
   - Parsing logic (file format handling) belongs to a separate module.
   - Validation & mapping belong to a middle layer (logic) that is pure and testable.
   - Persistence belongs to a database module.

2. **API contracts**:
   - Parsers should return a list of (table_name, table_data) where table_data is a simple tabular structure (DataFrame or list-of-maps).
   - Logic should accept that structure and return a report with keys: mapping, sanitized_table, validation, sanitize_logs.
   - Persistence should accept a tabular structure and table_name and provide options for conflict handling (replace/append/fail).

3. **UI patterns**:
   - Preview before commit (very important for data import tools).
   - Use human-friendly summaries for generic tables (first 3 columns) and specialized views for known schemas.
   - Fail fast with clear errors for user mistakes (e.g., missing DB selection).

4. **Testing**:
   - Unit-test parsers with real sample files (CSV/Excel/PDF/image).
   - Test validation & auto-fix on corner cases: currency formatting, negative numbers, missing names.
   - GUI tests: simulate user selecting file and confirming commit (where possible).

---

## 4) Example: Translating the pattern to a web UI (React + Node)

- Parsers & logic: implement as Node services (or Python microservice) that expose endpoints:
  - `POST /preview` -> returns preview+validation
  - `POST /import` -> performs commit
- Persistence: Node service uses sqlite/sequelize or a full DB; mimic `if_exists` behavior in SQL layer.
- Frontend: React modal shows preview and allows renaming and toggling fixes before calling `/import`.

---

## 5) Common pitfalls & remedies

- **Large files**: Pandas in-memory ingestion can OOM. Remedy: stream or chunk when parsing CSVs.
- **OCR noise**: OCR results need manual review; always present previews and don't auto-commit.
- **Schema ambiguity**: Column names are brittle; prefer user-mapped fields or a saved-mapping feature.

---

## 6) Quick reference: Useful commands

- Run GUI locally:

  ```bash
  python gui_documented.py
  ```

- Preview import manually (CLI using core.logic):

  ```bash
  python -c "from core import logic; print(logic.preview_and_analyze('specs.xlsx'))"
  ```

---

## 7) Next improvements you can implement (small projects)

- Add a preview modal in the GUI that integrates `core.logic.preview_and_analyze`.
- Implement per-row progress when writing large tables (batch writes + progress callback).
- Support custom mapping templates: let users save a JSON mapping and apply it to similar files.
- Add unit tests with pytest fixtures and small sample files for CSV/Excel/PDF/images.

---

If you'd like, I can now:
- Implement the preview modal (Tkinter) and wire it to `core.logic.preview_and_analyze`, or
- Generate a small test-suite (pytest) that includes sample CSVs/Excel files and verifies mapping + import.

Pick one and I'll implement it right away.


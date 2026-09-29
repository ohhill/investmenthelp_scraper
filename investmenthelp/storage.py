"""CSV storage for advisor records."""

import csv
import os

from investmenthelp.api import FIELDS


def load_csv(path):
    """Return {cst_no: row} from an existing CSV, or {} if the file does not exist."""
    rows = {}
    if os.path.exists(path):
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("cst_no", "").isdigit():
                    rows[int(row["cst_no"])] = row
    return rows


def open_writer(path, overwrite):
    """Open the CSV for appending (or overwriting with a fresh header). Returns (file, writer)."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    f = open(path, "w" if overwrite else "a", newline="", encoding="utf-8")
    writer = csv.DictWriter(f, fieldnames=FIELDS)
    if overwrite:
        writer.writeheader()
    return f, writer


def save_sorted(path, rows):
    """Rewrite the CSV with rows ({cst_no: row}) sorted by ID."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows[k] for k in sorted(rows))

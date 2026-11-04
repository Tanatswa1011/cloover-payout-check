"""Load the invented sample projects from CSV into plain dictionaries."""
import csv
from datetime import date
from pathlib import Path

SAMPLE_FILE = Path(__file__).parent / "sample_projects.csv"
NUMBERS = {"kwp", "quote", "requested", "financed", "invoice", "installed_kwp", "battery_kwh", "installed_battery_kwh", "photos"}
YES_NO = {"quote_doc", "assessment", "cert"}
DATES = {"contract_date", "install_date", "invoice_date"}
TEXT_KEEP = {"postcode", "account", "registered_account"}  # keep leading zeros


def load_projects(path: Path = SAMPLE_FILE) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [_convert(row) for row in csv.DictReader(f)]


def _convert(row: dict) -> dict:
    project = {}
    for key, value in row.items():
        value = value.strip()
        if key in NUMBERS:
            project[key] = (int(value) if key == "photos" else float(value)) if value else None
        elif key in YES_NO:
            project[key] = value == "yes"
        elif key in DATES:
            project[key] = date.fromisoformat(value) if value else None
        else:
            project[key] = value or None
    return project

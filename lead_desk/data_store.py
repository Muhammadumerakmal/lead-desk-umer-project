"""
Everything the language model is *not* allowed to see directly.

The agent never receives rates.json or availability.json in its prompt or
context. It only ever learns these numbers by calling a tool, and only
receives back whatever that tool's return value says — the same boundary
you'd want if this data lived in a real database instead of a JSON file.
"""

from __future__ import annotations

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RATES_FILE = DATA_DIR / "rates.json"
AVAILABILITY_FILE = DATA_DIR / "availability.json"
LEADS_FILE = DATA_DIR / "leads.json"


def read_rates() -> dict:
    return json.loads(RATES_FILE.read_text())


def read_availability() -> dict:
    return json.loads(AVAILABILITY_FILE.read_text())


def append_lead(record: dict) -> None:
    leads = []
    if LEADS_FILE.exists():
        try:
            leads = json.loads(LEADS_FILE.read_text())
        except json.JSONDecodeError:
            leads = []
    leads.append(record)
    LEADS_FILE.write_text(json.dumps(leads, indent=2))

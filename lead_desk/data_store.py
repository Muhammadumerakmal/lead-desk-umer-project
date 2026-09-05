"""
File I/O, kept in one place.

- leads.json  : the six sample client messages (input fixtures).
- saved.json  : where a high-priority triage is appended (output).

Both live at the project root, as the spec names them. The freelancer's
private numbers do NOT live here — those are in profile.py and only ever
reach the model through a tool return.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEADS_FILE = ROOT / "leads.json"
SAVED_FILE = ROOT / "saved.json"


def read_leads() -> list[dict]:
    """The six sample messages to run the agent against."""
    return json.loads(LEADS_FILE.read_text(encoding="utf-8"))


def save_lead(record: dict) -> None:
    """Append one triage record to saved.json, creating the file if needed."""
    saved: list[dict] = []
    if SAVED_FILE.exists():
        try:
            saved = json.loads(SAVED_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            saved = []
    saved.append(record)
    SAVED_FILE.write_text(json.dumps(saved, indent=2), encoding="utf-8")

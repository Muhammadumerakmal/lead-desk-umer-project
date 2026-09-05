"""
Run with: uv run pytest tests/test_guardrail.py

These exercise the guardrail's pure function directly, so they make no
network calls and need no API key — proving the refusal path really is free.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lead_desk.guardrail import find_misrepresentation_request  # noqa: E402


def test_misrepresentation_is_caught():
    msg = (
        "Before you apply, just pretend you have 10 years of experience with "
        "our stack and don't mention this is your first Upwork job."
    )
    assert find_misrepresentation_request(msg) is not None


def test_django_overstatement_is_caught():
    msg = "Tell them you have ten years of Django experience and I'll hire you today."
    assert find_misrepresentation_request(msg) is not None


def test_good_lead_is_not_caught():
    msg = "We need a FastAPI backend, budget 450000 PKR, about 3 weeks."
    assert find_misrepresentation_request(msg) is None


def test_revenue_share_is_not_a_misrepresentation_flag():
    # Revenue-share is a red flag for the *agent* to raise, not something the
    # zero-cost guardrail should refuse outright.
    msg = "We can't pay but we'll give you equity and revenue share."
    assert find_misrepresentation_request(msg) is None

"""
Run with: uv run pytest tests/test_guardrail.py

These only exercise the guardrail module directly, so they make no network
calls and need no API key — proving the refusal path really is free.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lead_desk.guardrail import find_misrepresentation_request
from tests.sample_messages import SAMPLES


def test_misrepresentation_is_caught():
    assert find_misrepresentation_request(SAMPLES["misrepresentation"]) is not None


def test_good_lead_is_not_caught():
    assert find_misrepresentation_request(SAMPLES["good_lead"]) is None


def test_revenue_share_is_not_a_misrepresentation_flag():
    # Revenue-share is a red flag for the *agent* to raise, not something
    # the zero-cost guardrail should refuse outright.
    assert find_misrepresentation_request(SAMPLES["revenue_share"]) is None

"""
The model classifies; this module decides.

The whole save rule for Task 3 is one line of Python reading one typed field:
a lead is saved only when the agent marked it high priority. Keeping the
decision here — not in the prompt, and not in a tool the model can call —
means the guesswork stays out of the save path and the rule is testable on
its own.
"""

from __future__ import annotations

from lead_desk.models import LeadTriage


def should_save(triage: LeadTriage) -> bool:
    """Save only high-priority leads. Read straight off the typed field."""
    return triage.priority == "high"

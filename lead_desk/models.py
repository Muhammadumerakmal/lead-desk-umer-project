"""
Typed contracts for Lead Desk.

LeadVerdict is what the agent (the language model) is asked to produce.
LeadDecision is what our own Python code produces afterwards, by combining
the verdict with facts read straight from disk (rate + availability) that
the model never saw directly — it only ever saw whatever a tool call
returned to it.

Keeping these as two separate models is deliberate: the model classifies,
Python decides. If we let the model set `worth_pursuing` itself, a single
bad classification could silently save (or drop) a lead with no code path
to audit or override.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Intent(str, Enum):
    NEW_PROJECT = "new_project"       # a scoped build the client wants started
    QUICK_TASK = "quick_task"          # small, bounded, one-off ask
    CONSULTATION = "consultation"      # advice / audit / call, not a build
    ONGOING_ROLE = "ongoing_role"      # retainer, part-time, long-term hire
    VAGUE = "vague"                    # not enough info to tell yet
    SPAM = "spam"                      # not a real lead at all


class RedFlag(str, Enum):
    NO_BUDGET_MENTIONED = "no_budget_mentioned"
    REVENUE_SHARE_OR_EQUITY = "revenue_share_or_equity"
    UNREALISTIC_TIMELINE = "unrealistic_timeline"
    SCOPE_IS_OPEN_ENDED = "scope_is_open_ended"
    LOWBALL_BUDGET = "lowball_budget"
    ASKS_FOR_FREE_SAMPLE_WORK = "asks_for_free_sample_work"
    PRESSURE_TACTICS = "pressure_tactics"
    MISREPRESENTATION_REQUEST = "misrepresentation_request"


class LeadVerdict(BaseModel):
    """The agent's structured read of the raw client message."""

    intent: Intent
    one_line_summary: str = Field(
        ..., description="What the client actually wants, in one plain sentence."
    )
    stated_budget_usd: float | None = Field(
        default=None,
        description="Numeric USD budget the client stated or clearly implied. "
        "Null if no budget was mentioned at all.",
    )
    estimated_hours: float | None = Field(
        default=None,
        description="Your best-effort estimate of hours the described work "
        "would take. Null if there isn't enough detail to estimate.",
    )
    red_flags: list[RedFlag] = Field(default_factory=list)
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="How confident you are in this reading."
    )


class LeadDecision(BaseModel):
    """
    The final, program-actionable outcome. Built entirely in Python from a
    LeadVerdict plus the rate card and availability tools returned — the
    model never fills this in.
    """

    verdict: LeadVerdict
    hourly_rate_usd: float
    free_hours_this_week: float
    implied_budget_hours: float | None
    worth_pursuing: bool
    reason: str
    saved: bool

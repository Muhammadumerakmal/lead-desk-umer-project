"""
The model classifies. This module decides.

Nothing here calls the language model — it takes the LeadVerdict the agent
already produced, reads the rate card and availability straight from disk
(the same source the agent's tools read from), and applies plain rules to
arrive at a LeadDecision. Keeping this in Python means the "is this worth
my time" call is auditable and testable independent of the model, and a
model that under- or over-estimates a budget doesn't get the final word on
whether a lead gets saved.
"""

from __future__ import annotations

from lead_desk.data_store import read_availability, read_rates
from lead_desk.models import LeadDecision, LeadVerdict, RedFlag

# Red flags severe enough, on their own, to make a lead not worth pursuing
# regardless of budget.
_DISQUALIFYING_FLAGS = {
    RedFlag.MISREPRESENTATION_REQUEST,
}

# Red flags that count against a lead but don't disqualify it outright.
_SOFT_NEGATIVE_FLAGS = {
    RedFlag.REVENUE_SHARE_OR_EQUITY,
    RedFlag.LOWBALL_BUDGET,
    RedFlag.ASKS_FOR_FREE_SAMPLE_WORK,
    RedFlag.PRESSURE_TACTICS,
}


def evaluate(verdict: LeadVerdict) -> LeadDecision:
    rates = read_rates()
    availability = read_availability()

    hourly_rate = float(rates["hourly_rate_usd"])
    min_budget = float(rates["minimum_project_budget_usd"])
    free_hours_this_week = float(availability["free_hours_this_week"])
    free_hours_next_week = float(availability["free_hours_next_week"])
    currently_booked = bool(availability["currently_booked"])

    implied_budget_hours = None
    if verdict.stated_budget_usd:
        implied_budget_hours = round(verdict.stated_budget_usd / hourly_rate, 1)

    reasons: list[str] = []
    worth_pursuing = True

    if verdict.intent.value == "spam":
        worth_pursuing = False
        reasons.append("classified as spam")

    disqualifying = _DISQUALIFYING_FLAGS.intersection(verdict.red_flags)
    if disqualifying:
        worth_pursuing = False
        reasons.append(f"disqualifying red flag(s): {', '.join(f.value for f in disqualifying)}")

    if worth_pursuing and verdict.stated_budget_usd is not None:
        if verdict.stated_budget_usd < min_budget:
            worth_pursuing = False
            reasons.append(
                f"stated budget ${verdict.stated_budget_usd:.0f} is below the "
                f"${min_budget:.0f} minimum"
            )

    if worth_pursuing and verdict.stated_budget_usd is None:
        # No budget stated at all is only a soft signal on its own — but
        # combined with vague scope it's not worth chasing.
        if verdict.intent.value == "vague" or RedFlag.NO_BUDGET_MENTIONED in verdict.red_flags:
            if RedFlag.SCOPE_IS_OPEN_ENDED in verdict.red_flags:
                worth_pursuing = False
                reasons.append("no budget stated and scope is open-ended")

    if worth_pursuing and currently_booked and free_hours_next_week <= 0:
        worth_pursuing = False
        reasons.append("no free hours this week or next")

    soft_hits = _SOFT_NEGATIVE_FLAGS.intersection(verdict.red_flags)
    if worth_pursuing and len(soft_hits) >= 2:
        worth_pursuing = False
        reasons.append(
            f"too many soft red flags: {', '.join(f.value for f in soft_hits)}"
        )

    if worth_pursuing:
        reasons.append("passes budget, scope, and availability checks")

    return LeadDecision(
        verdict=verdict,
        hourly_rate_usd=hourly_rate,
        free_hours_this_week=free_hours_this_week,
        implied_budget_hours=implied_budget_hours,
        worth_pursuing=worth_pursuing,
        reason="; ".join(reasons),
        saved=False,  # set by the caller once/if it actually persists the lead
    )

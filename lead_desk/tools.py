"""
Tools exposed to the agent. Each one reads from disk in Python and returns
only a small, deliberate slice of that data back to the model — this is the
boundary that keeps the rate card and calendar out of the model's context.
"""

from __future__ import annotations

from agents import function_tool

from lead_desk.data_store import read_availability, read_rates


@function_tool
def get_my_rate() -> dict:
    """Return the freelancer's current hourly rate and minimum engagement
    terms. Use this whenever you need to reason about whether a stated or
    implied budget is realistic."""
    rates = read_rates()
    return {
        "hourly_rate_usd": rates["hourly_rate_usd"],
        "minimum_engagement_hours": rates["minimum_engagement_hours"],
        "minimum_project_budget_usd": rates["minimum_project_budget_usd"],
    }


@function_tool
def get_my_availability() -> dict:
    """Return how many free hours the freelancer has this week and next,
    and whether they're currently booked solid. Use this to judge whether
    a client's timeline is realistic."""
    availability = read_availability()
    return {
        "free_hours_this_week": availability["free_hours_this_week"],
        "free_hours_next_week": availability["free_hours_next_week"],
        "currently_booked": availability["currently_booked"],
    }

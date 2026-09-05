"""
The two tools the agent is given.

Both take a `RunContextWrapper[FreelancerProfile]` as their first parameter.
That parameter is the boundary: the SDK strips it out of the JSON schema it
shows the model (see `uv run lead-desk --schema`), so the model can *call*
these tools but never sees the private numbers they read from. The model
only receives whatever we choose to return.
"""

from __future__ import annotations

from agents import RunContextWrapper, function_tool

from lead_desk.profile import FreelancerProfile


@function_tool
def lookup_rate_card(
    ctx: RunContextWrapper[FreelancerProfile], skill: str
) -> dict:
    """Look up the freelancer's hourly rate (in PKR) for a given skill.

    Call this before you discuss money. Pass the single skill the client's
    request is really about (e.g. "python", "fastapi", "web scraping"). If
    the skill is not one the freelancer offers, this returns no rate and you
    must tell the client you do not have a rate for it rather than inventing
    a number.
    """
    profile = ctx.context
    known = {s.lower() for s in profile.skills}
    if skill.strip().lower() in known:
        return {"skill": skill, "hourly_rate_pkr": profile.min_rate_pkr_hour}
    return {
        "skill": skill,
        "hourly_rate_pkr": None,
        "note": "No rate on file for this skill.",
    }


@function_tool
def check_availability(
    ctx: RunContextWrapper[FreelancerProfile], week: str
) -> dict:
    """Return how many hours the freelancer has free in the given week.

    `week` is a plain label such as "this week" or "next week". Use this to
    judge whether a client's timeline is realistic before you comment on it.
    """
    profile = ctx.context
    return {"week": week, "free_hours": profile.hours_free_per_week}


def _profile_is_verified(
    ctx: RunContextWrapper[FreelancerProfile], agent
) -> bool:
    """Gate for send_proposal. The SDK calls this while resolving the tool
    list; if it returns False the tool is never sent to the model at all."""
    return bool(ctx.context.verified)


@function_tool(is_enabled=_profile_is_verified)
def send_proposal(
    ctx: RunContextWrapper[FreelancerProfile],
    client_message: str,
    proposed_rate_pkr: int,
) -> dict:
    """Send a formal proposal to the client at the given hourly rate (PKR).

    Only available to verified freelancers. Use this once you are confident
    the lead is worth pursuing and you have a rate to quote.
    """
    profile = ctx.context
    return {
        "sent": True,
        "from": profile.name,
        "proposed_rate_pkr": proposed_rate_pkr,
        "re": client_message[:60],
    }

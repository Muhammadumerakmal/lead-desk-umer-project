"""
The freelancer's private data — the stuff the language model must never see.

Task 2 hinges on one idea: your minimum rate is negotiating leverage, so it
cannot live in the system prompt or in any message. It lives here, in a
FreelancerProfile, which we hand to the run *as context*. The tools read
their answers out of this object; the model only ever sees whatever a tool
chooses to return. Search this file for `min_rate_pkr_hour` and you will
find the number — search the instructions or any message and you will not.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class FreelancerProfile(BaseModel):
    """Private context for a run. Never serialised into a prompt or message."""

    name: str
    min_rate_pkr_hour: int = Field(
        ..., description="The lowest hourly rate (PKR) you will accept. Secret."
    )
    skills: list[str] = Field(
        ..., description="Skills you actually offer. A skill not on this list "
        "has no rate on file, so the agent must say it does not know."
    )
    hours_free_per_week: int = Field(
        ..., description="How many hours you have free in a typical week."
    )
    verified: bool = Field(
        default=False, description="Whether your identity/experience is verified."
    )


def build_profile() -> FreelancerProfile:
    """The single private profile this program runs with."""
    return FreelancerProfile(
        name="Muhammad Ali Akmal",
        min_rate_pkr_hour=6000,
        skills=[
            "python",
            "fastapi",
            "backend",
            "web scraping",
            "automation",
            "agents",
        ],
        hours_free_per_week=20,
        verified=False,
    )

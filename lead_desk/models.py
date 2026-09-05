"""
The one typed shape the agent returns.

Prose cannot be branched on. `LeadTriage` is a class, so `budget_pkr` is a
real integer you can do arithmetic on and `priority` is a fixed set of
values your `if` statement can read. The model fills this in; your Python
code (see decision.py / cli.py) reads it and decides what to do.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Priority = Literal["high", "medium", "low"]


class LeadTriage(BaseModel):
    """The agent's structured verdict on one raw client message."""

    intent: str = Field(
        ..., description="A short phrase for what the client wants, e.g. "
        "'new backend build', 'quick fix', 'too vague to tell'."
    )
    budget_pkr: int | None = Field(
        default=None,
        description="The client's stated or clearly implied budget in PKR, as "
        "a whole number. Leave absent (null) if no budget was mentioned.",
    )
    red_flags: list[str] = Field(
        default_factory=list,
        description="Short phrases naming anything risky: no budget, revenue "
        "share instead of pay, unrealistic deadline, open-ended scope, "
        "pressure tactics. Empty only if the message genuinely has none.",
    )
    priority: Priority = Field(
        ..., description="'high' for a serious, well-scoped, paying lead worth "
        "replying to fast; 'medium' if it needs clarifying; 'low' for noise."
    )
    suggested_reply: str = Field(
        ..., description="A short, professional reply you could send the client."
    )

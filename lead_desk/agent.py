"""
The Lead Desk agent: one Agent, two lookup tools, one input guardrail, and
one typed output shape (LeadTriage).

It runs on Gemini's gemini-2.5-flash through Google's OpenAI-compatible
endpoint, which is why we build an AsyncOpenAI client pointed at Google and
wrap it in OpenAIChatCompletionsModel rather than passing a bare model name.
"""

from __future__ import annotations

import os

from agents import Agent, OpenAIChatCompletionsModel, set_tracing_disabled
from dotenv import load_dotenv
from openai import AsyncOpenAI

from lead_desk.guardrail import misrepresentation_guardrail
from lead_desk.models import LeadTriage
from lead_desk.profile import FreelancerProfile
from lead_desk.tools import check_availability, lookup_rate_card, send_proposal

load_dotenv()

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

# The SDK's default tracing exporter wants an OpenAI key we don't have, so we
# turn tracing off rather than let it fail noisily.
set_tracing_disabled(True)


def _build_model() -> OpenAIChatCompletionsModel:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Copy .env.example to .env and fill it in."
        )
    client = AsyncOpenAI(api_key=api_key, base_url=GEMINI_BASE_URL)
    # The spec asks for gemini-2.5-flash, but Google now returns a 404 for it
    # ("no longer available to new users. Please update ... to gemini-3.6-flash").
    # We use 3.6-flash so the agent actually runs; the wiring is identical.
    model_name = os.environ.get("LEAD_DESK_MODEL", "gemini-3.6-flash")
    return OpenAIChatCompletionsModel(model=model_name, openai_client=client)


# Note what is NOT here: no rate, no free-hours figure, no minimum price. The
# model learns those only by calling a tool. That is the whole point of Task 2.
INSTRUCTIONS = """\
You are Lead Desk, triaging one raw freelance client message at a time.

Your job is to read the message and return a structured verdict. Work out:
- the intent: a short phrase for what the client actually wants
- the budget in PKR, as a whole number, if one is stated or clearly implied
- any red flags in how the message is written
- a priority: high, medium, or low
- a short, professional suggested reply

Before you comment on whether a budget or timeline is realistic, call
lookup_rate_card with the skill the request is about, and call
check_availability for the relevant week. Never guess the freelancer's rate
or free hours — those tools are the only source of truth. If lookup_rate_card
returns no rate for a skill, say you don't have a rate for it; do not invent
one.

Be skeptical. No budget, "exposure", "revenue share instead of pay", "quick
job should take an hour", unrealistic turnarounds, open-ended scope, and
pressure ("today or we go elsewhere") are all red flags worth naming even if
the client sounds friendly. Only leave red_flags empty if there genuinely
are none.

Set priority to 'high' only for a serious, well-scoped lead that looks worth
replying to fast; 'medium' when it needs clarifying before you could quote;
'low' for noise. You classify only — you do not decide whether the lead gets
saved. That decision is made by code outside you.
"""


def build_agent() -> Agent[FreelancerProfile]:
    return Agent[FreelancerProfile](
        name="Lead Desk",
        instructions=INSTRUCTIONS,
        model=_build_model(),
        # send_proposal is listed here always, but its is_enabled gate means
        # the SDK only offers it to the model when profile.verified is True.
        tools=[lookup_rate_card, check_availability, send_proposal],
        input_guardrails=[misrepresentation_guardrail],
        output_type=LeadTriage,
    )

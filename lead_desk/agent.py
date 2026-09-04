"""
The Lead Desk agent itself: one Agent, two tools, one typed output.

Runs on Gemini through its OpenAI-compatible endpoint, which is why we
build an AsyncOpenAI client pointed at Google instead of OpenAI and wrap it
in OpenAIChatCompletionsModel rather than passing a bare model name.
"""

from __future__ import annotations

import os

from agents import Agent, OpenAIChatCompletionsModel, set_tracing_disabled
from dotenv import load_dotenv
from openai import AsyncOpenAI

from lead_desk.models import LeadVerdict
from lead_desk.tools import get_my_availability, get_my_rate

load_dotenv()

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

# The SDK's default tracing exporter expects an OpenAI API key. We're not
# using OpenAI at all here, so tracing is disabled rather than left to fail
# silently or demand a key we don't need.
set_tracing_disabled(True)


def _build_model() -> OpenAIChatCompletionsModel:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Copy .env.example to .env and fill it in."
        )
    client = AsyncOpenAI(api_key=api_key, base_url=GEMINI_BASE_URL)
    model_name = os.environ.get("LEAD_DESK_MODEL", "gemini-2.5-flash")
    return OpenAIChatCompletionsModel(model=model_name, openai_client=client)


INSTRUCTIONS = """\
You are Lead Desk, triaging one raw freelance client message at a time.

Your job is to classify, not to negotiate and not to reply to the client.
Work out:
- what the client actually wants (intent + a one-line plain summary)
- what budget they stated or clearly implied, if any
- roughly how many hours the described work would take
- any red flags in how the message is written

Before judging whether a budget or timeline is realistic, call
get_my_rate and get_my_availability. Don't guess at the freelancer's rate
or free time — those tools are the only source of truth for them.

Be skeptical. Vague scope, no budget, "exposure", "revenue share instead
of pay", unrealistic turnarounds, and pressure ("need this today or we'll
find someone else") are all red flags worth flagging even if the client
sounds friendly. Only mark red_flags empty if the message genuinely has
none.

You always return a LeadVerdict. You never draft a reply to the client
and you never decide whether to pursue the lead — that decision is made
outside of you.
"""


def build_agent() -> Agent:
    return Agent(
        name="Lead Desk",
        instructions=INSTRUCTIONS,
        model=_build_model(),
        tools=[get_my_rate, get_my_availability],
        output_type=LeadVerdict,
    )

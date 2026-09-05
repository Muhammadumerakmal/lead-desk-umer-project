"""
An input guardrail that refuses before you pay.

A message asking you to lie about your experience should never reach the
model — processing it costs money and the only correct answer is "no". This
guardrail is pure Python pattern matching: it makes no API call, so a
blocked message is refused instantly. It trips the SDK's tripwire, which the
CLI catches and turns into a polite decline (an *uncaught* tripwire would be
a crash, not a refusal).

`find_misrepresentation_request` is kept as a plain function so it can be
unit-tested with no SDK or network involved.
"""

from __future__ import annotations

import re

from agents import (
    GuardrailFunctionOutput,
    RunContextWrapper,
    TResponseInputItem,
    input_guardrail,
)

# Patterns that indicate the client wants the freelancer to misrepresent who
# they are or what they have done. Blunt on purpose — a regex costs nothing.
_MISREPRESENTATION_PATTERNS = [
    r"\bpretend (you|to be|to have)\b",
    r"\bsay you('| a)?re? (a|an)?\s*(senior|expert|certified|native)\b",
    r"\bclaim(ed|ing)? (you|to have)\b",
    r"\blie about\b",
    r"\bfake (your|a|the)?\s*(portfolio|experience|review|testimonial|degree|certificat)",
    r"\bmake up (a|an|your)\s*(portfolio|experience|case stud|reference)",
    r"\bexaggerate your\b",
    r"\bpose as\b",
    r"\btell (them|the client) (that )?you have\b.*\b(years?|experience)\b",
    r"\bdon'?t (mention|tell them) (that )?you('re| are)? (a )?(beginner|new|junior|student)",
    r"\bwrite (a )?fake (review|testimonial)",
    r"\boverstate your\b",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in _MISREPRESENTATION_PATTERNS]

REFUSAL_REASON = (
    "This message asks me to misrepresent my experience or credentials, "
    "which I won't do. I'm happy to help on the basis of my actual skills."
)


def find_misrepresentation_request(message: str) -> str | None:
    """Return a plain-text reason if the message asks the freelancer to
    misrepresent themselves, else None. No side effects, no network."""
    for pattern in _COMPILED:
        if pattern.search(message):
            return REFUSAL_REASON
    return None


def _as_text(agent_input: str | list[TResponseInputItem]) -> str:
    """The guardrail input can be a bare string or a list of input items;
    flatten it to text so the regex has something to scan."""
    if isinstance(agent_input, str):
        return agent_input
    parts: list[str] = []
    for item in agent_input:
        content = item.get("content") if isinstance(item, dict) else None
        if isinstance(content, str):
            parts.append(content)
    return " ".join(parts)


@input_guardrail
async def misrepresentation_guardrail(
    ctx: RunContextWrapper,
    agent,
    agent_input: str | list[TResponseInputItem],
) -> GuardrailFunctionOutput:
    """Trips the tripwire (no model call) when the message asks the
    freelancer to misrepresent themselves."""
    reason = find_misrepresentation_request(_as_text(agent_input))
    return GuardrailFunctionOutput(
        output_info=reason,
        tripwire_triggered=reason is not None,
    )

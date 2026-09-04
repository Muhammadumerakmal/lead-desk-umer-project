"""
A message that's asking you to misrepresent yourself doesn't need an LLM
to classify it — it needs to be refused, immediately, in plain Python,
before a single token is sent anywhere. That's the point: this check runs
first and short-circuits the whole pipeline, so a matching message costs
zero API calls.

This is intentionally a blunt keyword/pattern check rather than a model
call. A model-based guardrail is still an API call; this one isn't.
"""

from __future__ import annotations

import re

# Patterns that indicate the client is asking the freelancer to lie about
# who they are or what they've done. Kept as compiled regexes so this stays
# fast and dependency-free.
_MISREPRESENTATION_PATTERNS = [
    r"\bpretend (you|to be)\b",
    r"\bsay you('| a)?re? (a|an)?\s*(senior|expert|certified|native)\b",
    r"\bclaim(ed|ing)? (you|to have)\b",
    r"\blie about\b",
    r"\bfake (your|a|the)?\s*(portfolio|experience|review|testimonial|degree|certificat)",
    r"\bmake up (a|an|your)\s*(portfolio|experience|case stud|reference)",
    r"\bexaggerate your\b",
    r"\bpose as\b",
    r"\bpretend to have\b",
    r"\bwe('ll| will) (just )?tell (them|the client) you\b",
    r"\bdon'?t (mention|tell them) (that )?you('re| are)? (a )?(beginner|new|junior|student)",
    r"\bwrite (a )?fake (review|testimonial)",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in _MISREPRESENTATION_PATTERNS]


def find_misrepresentation_request(message: str) -> str | None:
    """Return the matched pattern's plain-text reason if the message asks
    the freelancer to misrepresent themselves, else None."""
    for pattern in _COMPILED:
        if pattern.search(message):
            return (
                "Message asks the freelancer to misrepresent their "
                "experience, identity, or credentials."
            )
    return None

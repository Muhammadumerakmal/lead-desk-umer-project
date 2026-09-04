"""
Entry point. Usage:

    uv run lead-desk "the raw client message goes here"

or, without an argument, it reads the message from stdin so you can pipe
messages in one at a time.

Pipeline:
    1. guardrail check (zero API calls) — refuse and stop if it fires
    2. agent call -> LeadVerdict (typed, not prose)
    3. decision.evaluate() -> LeadDecision (pure Python)
    4. save to data/leads.json only if worth_pursuing is True
"""

from __future__ import annotations

import json
import sys

from agents import Runner

from lead_desk.agent import build_agent
from lead_desk.data_store import append_lead
from lead_desk.decision import evaluate
from lead_desk.guardrail import find_misrepresentation_request


def _get_message() -> str:
    if len(sys.argv) > 1:
        return " ".join(sys.argv[1:])
    message = sys.stdin.read().strip()
    if not message:
        print("Usage: lead-desk \"<client message>\"  (or pipe a message via stdin)")
        sys.exit(1)
    return message


def run(message: str) -> dict:
    refusal_reason = find_misrepresentation_request(message)
    if refusal_reason:
        result = {
            "refused": True,
            "reason": refusal_reason,
            "api_calls_made": 0,
        }
        return result

    agent = build_agent()
    run_result = Runner.run_sync(agent, message)
    verdict = run_result.final_output  # a LeadVerdict, guaranteed by output_type

    decision = evaluate(verdict)

    if decision.worth_pursuing:
        record = decision.model_dump(mode="json")
        record["original_message"] = message
        append_lead(record)
        decision.saved = True

    return {
        "refused": False,
        "decision": decision.model_dump(mode="json"),
    }


def main() -> None:
    message = _get_message()
    output = run(message)
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()

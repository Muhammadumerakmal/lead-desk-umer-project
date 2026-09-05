"""
Entry point. Everything runs through the asynchronous runner.

Usage:
    uv run lead-desk                     # triage one hardcoded message
    uv run lead-desk "client message"    # triage the message you pass
    uv run lead-desk --all               # triage all six fixtures in leads.json
    uv run lead-desk --schema            # print a tool's JSON schema (evidence)

Pipeline per message:
    1. input guardrail (zero API calls) — refuse and stop if it trips
    2. agent run -> LeadTriage (typed, not prose)
    3. Python decides: save only when priority == "high"
    4. one-line banner, then append to saved.json
"""

from __future__ import annotations

import asyncio
import json
import sys

from agents import InputGuardrailTripwireTriggered, Runner
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from lead_desk.agent import build_agent
from lead_desk.data_store import read_leads, save_lead
from lead_desk.decision import should_save
from lead_desk.guardrail import REFUSAL_REASON
from lead_desk.models import LeadTriage
from lead_desk.profile import build_profile
from lead_desk.tools import lookup_rate_card

console = Console()

# Task 0: the one hardcoded message used when no argument is given.
HARDCODED_MESSAGE = (
    "Hi! We need a FastAPI backend for an internal dashboard, about 3 weeks "
    "of work. Budget is around 400000 PKR. Can you start next week?"
)


def _print_schema() -> None:
    """Task 2 evidence: the model-visible schema of a tool. The private
    context parameter does not appear here — only `skill` does."""
    schema = lookup_rate_card.params_json_schema
    console.print(
        Panel(
            json.dumps(schema, indent=2),
            title="lookup_rate_card — JSON schema shown to the model",
            border_style="magenta",
        )
    )
    console.print(
        "[dim]Note: no `ctx` / context parameter appears — the SDK strips it, "
        "so the private profile never reaches the model.[/dim]"
    )


def _print_triage(triage: LeadTriage) -> None:
    table = Table(show_header=False, border_style="cyan", padding=(0, 2))
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Intent", triage.intent)
    table.add_row(
        "Budget",
        f"{triage.budget_pkr:,} PKR" if triage.budget_pkr is not None
        else "[dim]not stated[/dim]",
    )
    priority_colour = {"high": "green", "medium": "yellow", "low": "red"}[
        triage.priority
    ]
    table.add_row("Priority", f"[{priority_colour}]{triage.priority}[/{priority_colour}]")
    table.add_row(
        "Red Flags",
        "[red]" + "; ".join(triage.red_flags) + "[/red]" if triage.red_flags
        else "[green]none[/green]",
    )
    table.add_row("Suggested Reply", triage.suggested_reply)
    console.print(table)


async def triage_one(message: str) -> None:
    """Run one message through guardrail -> agent -> save decision."""
    profile = build_profile()
    agent = build_agent()

    try:
        result = await Runner.run(agent, message, context=profile)
    except InputGuardrailTripwireTriggered:
        # No model call was made. Decline politely and return cleanly.
        console.print(Panel(REFUSAL_REASON, title="[red]Refused[/red]",
                            border_style="red"))
        return

    triage: LeadTriage = result.final_output
    _print_triage(triage)

    # The save decision is Python's, reading the typed priority field.
    if should_save(triage):
        budget = triage.budget_pkr if triage.budget_pkr is not None else "n/a"
        # One-line banner showing priority and budget before saving.
        console.print(
            f"[bold green][SAVE][/bold green] priority={triage.priority} "
            f"budget_pkr={budget}"
        )
        record = triage.model_dump()
        record["original_message"] = message
        save_lead(record)
    else:
        console.print(
            f"[dim][SKIP] priority={triage.priority} — not saved.[/dim]"
        )


async def _amain(argv: list[str]) -> None:
    if argv and argv[0] == "--schema":
        _print_schema()
        return

    if argv and argv[0] == "--all":
        for lead in read_leads():
            console.rule(f"[bold]{lead['id']}[/bold] · {lead['platform']}")
            console.print(f"[dim]{lead['message']}[/dim]")
            await triage_one(lead["message"])
        return

    message = " ".join(argv) if argv else HARDCODED_MESSAGE
    console.rule("[bold]Lead Desk[/bold]")
    console.print(f"[dim]{message}[/dim]")
    await triage_one(message)


def main() -> None:
    asyncio.run(_amain(sys.argv[1:]))


if __name__ == "__main__":
    main()

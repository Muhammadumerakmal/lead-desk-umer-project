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
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from lead_desk.agent import build_agent
from lead_desk.data_store import append_lead
from lead_desk.decision import evaluate
from lead_desk.guardrail import find_misrepresentation_request

console = Console()


def _get_message() -> str:
    if len(sys.argv) > 1:
        return " ".join(sys.argv[1:])
    message = sys.stdin.read().strip()
    if not message:
        console.print(
            '[red]Usage:[/red] lead-desk "[bold]<client message>[/bold]"  '
            "(or pipe a message via stdin)"
        )
        sys.exit(1)
    return message


def _print_refusal(reason: str) -> None:
    console.print()
    console.print(
        Panel(
            f"[bold red]REFUSED[/bold red]\n\n{reason}",
            title="[red]Guardrail Triggered[/red]",
            border_style="red",
        )
    )
    console.print()


def _print_decision(verdict, decision, message: str) -> None:
    console.print()

    # Header
    status = (
        "[bold green]WORTH PURSUING[/bold green]"
        if decision.worth_pursuing
        else "[bold yellow]NOT WORTH PURSUING[/bold yellow]"
    )
    console.print(Panel(status, title="Lead Desk Verdict", border_style="blue"))

    # Verdict table
    verdict_table = Table(
        title="AI Analysis", show_header=False, border_style="cyan", padding=(0, 2)
    )
    verdict_table.add_column("Field", style="bold")
    verdict_table.add_column("Value")

    verdict_table.add_row("Intent", verdict.intent)
    verdict_table.add_row("Summary", verdict.one_line_summary)
    verdict_table.add_row(
        "Budget",
        f"${verdict.stated_budget_usd:,.0f}"
        if verdict.stated_budget_usd
        else "[dim]Not stated[/dim]",
    )
    verdict_table.add_row("Est. Hours", f"{verdict.estimated_hours:.0f}h")
    verdict_table.add_row("Confidence", f"{verdict.confidence:.0%}")

    flags = verdict.red_flags
    if flags:
        verdict_table.add_row(
            "Red Flags", "[red]" + ", ".join(flags) + "[/red]"
        )
    else:
        verdict_table.add_row("Red Flags", "[green]None[/green]")

    console.print(verdict_table)

    # Decision table
    decision_table = Table(
        title="Decision", show_header=False, border_style="green", padding=(0, 2)
    )
    decision_table.add_column("Field", style="bold")
    decision_table.add_column("Value")

    decision_table.add_row("Hourly Rate", f"${decision.hourly_rate_usd:.0f}/hr")
    decision_table.add_row("Free Hours", f"{decision.free_hours_this_week:.0f}h")
    decision_table.add_row("Reason", decision.reason)

    if decision.saved:
        decision_table.add_row("Saved", "[green]Yes -> data/leads.json[/green]")

    console.print(decision_table)
    console.print()


def run(message: str) -> dict:
    refusal_reason = find_misrepresentation_request(message)
    if refusal_reason:
        _print_refusal(refusal_reason)
        return {
            "refused": True,
            "reason": refusal_reason,
            "api_calls_made": 0,
        }

    with console.status("[bold cyan]Analyzing message...[/bold cyan]", spinner="dots"):
        agent = build_agent()
        run_result = Runner.run_sync(agent, message)
        verdict = run_result.final_output

    decision = evaluate(verdict)

    if decision.worth_pursuing:
        record = decision.model_dump(mode="json")
        record["original_message"] = message
        append_lead(record)
        decision.saved = True

    _print_decision(verdict, decision, message)

    return {
        "refused": False,
        "decision": decision.model_dump(mode="json"),
    }


def main() -> None:
    message = _get_message()
    output = run(message)
    # Also dump raw JSON to stdout for piping
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()

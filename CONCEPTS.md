# Lead Desk — Concepts, line by line

This is a study/demo companion. Part A walks every source file line by line so
you can answer "what does this line do and why is it here" for any line the
examiner points at. Part B is the runtime story: what happens, in order, when
you run the program.

The core idea to keep in your head: **the model classifies, your Python
decides.** The language model reads a message and fills in a typed shape; it
never sees your private numbers and never decides what gets saved.

---

# Part A — File by file

## `lead_desk/profile.py` — the private data

```python
from __future__ import annotations
```
Lets you write type hints (like `list[str]`) that are evaluated lazily as
strings; harmless future-proofing, works on any 3.x.

```python
from pydantic import BaseModel, Field
```
Pydantic gives us a validated data class. `Field` lets us attach a description
and mark a field required.

```python
class FreelancerProfile(BaseModel):
```
The object that holds everything the model must **not** see. This is the
"context" for a run (Task 2).

```python
    name: str
    min_rate_pkr_hour: int = Field(..., description="... Secret.")
    skills: list[str] = Field(...)
    hours_free_per_week: int = Field(...)
    verified: bool = Field(default=False, ...)
```
The exact five fields Task 2 asks for. `...` (Ellipsis) means "required, no
default". `min_rate_pkr_hour` is the negotiating floor — the number that must
never reach the model. `verified` drives the Task 5B conditional tool.

```python
def build_profile() -> FreelancerProfile:
    return FreelancerProfile(name="...", min_rate_pkr_hour=6000, skills=[...],
                             hours_free_per_week=20, verified=False)
```
Constructs the one profile the program runs with. The secret rate lives here,
in source — Task 2 even says "search your own source for the number". It is in
no prompt and no message, which is what matters.

## `lead_desk/models.py` — the typed output

```python
from typing import Literal
Priority = Literal["high", "medium", "low"]
```
`Literal` restricts a value to exactly those three strings. This is what makes
`priority` safe to branch on — nothing else can end up in it.

```python
class LeadTriage(BaseModel):
    intent: str = Field(...)
    budget_pkr: int | None = Field(default=None, ...)
    red_flags: list[str] = Field(default_factory=list, ...)
    priority: Priority = Field(...)
    suggested_reply: str = Field(...)
```
The exact Task 3 shape. Why a class and not prose: you can do arithmetic on
`budget_pkr` (it's a real `int`), and `if triage.priority == "high"` works.
`int | None` = "an integer, or absent". `default_factory=list` gives each
instance its own empty list (never share a mutable default). The `description`
on each field is sent to the model as part of the schema, so good descriptions
make the model fill the shape correctly — this is prompt engineering through
types.

## `lead_desk/tools.py` — what the model can call

```python
from agents import RunContextWrapper, function_tool
```
`function_tool` turns a plain Python function into a tool the model can call.
`RunContextWrapper` is the SDK's carrier for your context object.

```python
@function_tool
def lookup_rate_card(ctx: RunContextWrapper[FreelancerProfile], skill: str) -> dict:
```
The decorator reads the signature and docstring to build the tool's JSON
schema. **Key concept:** the first param typed as `RunContextWrapper[...]` is
recognised as context and **excluded from the schema** — the model sees only
`skill`. That's how the tool reaches private data the model can't.

```python
    profile = ctx.context
    known = {s.lower() for s in profile.skills}
    if skill.strip().lower() in known:
        return {"skill": skill, "hourly_rate_pkr": profile.min_rate_pkr_hour}
    return {"skill": skill, "hourly_rate_pkr": None, "note": "No rate on file for this skill."}
```
`ctx.context` is the `FreelancerProfile` we passed to the run. We normalise
case with a set for an O(1) membership test. Known skill → return the rate;
unknown skill → return `None` with a note, so the model has to say "I don't
know" instead of inventing a number (Task 1 acceptance).

```python
@function_tool
def check_availability(ctx, week: str) -> dict:
    return {"week": week, "free_hours": profile.hours_free_per_week}
```
Same context pattern; returns free hours for a requested week label.

```python
def _profile_is_verified(ctx, agent) -> bool:
    return bool(ctx.context.verified)

@function_tool(is_enabled=_profile_is_verified)
def send_proposal(ctx, client_message: str, proposed_rate_pkr: int) -> dict:
```
Task 5B. `is_enabled` is a gate the SDK evaluates per run while assembling the
tool list. When it returns `False`, the tool's schema is never sent to the
model — the model literally cannot see or call it. `send_proposal` returns a
confirmation dict (it doesn't really send anything).

## `lead_desk/guardrail.py` — refuse before you pay

```python
import re
_MISREPRESENTATION_PATTERNS = [ r"\bpretend (you|to be|to have)\b", ... ]
_COMPILED = [re.compile(p, re.IGNORECASE) for p in _MISREPRESENTATION_PATTERNS]
```
A list of regexes for "lie about who you are" requests, compiled once for
speed. `\b` is a word boundary so we match whole words. `re.IGNORECASE` makes
it case-insensitive. **No LLM here** — that's the point of Task 4: this must
cost zero API calls.

```python
def find_misrepresentation_request(message: str) -> str | None:
    for pattern in _COMPILED:
        if pattern.search(message):
            return REFUSAL_REASON
    return None
```
Pure function: returns a reason string on the first matching pattern, else
`None`. Pure = testable with no key and no network.

```python
def _as_text(agent_input) -> str:
```
The guardrail input can be a plain string or a list of message items; this
flattens either into text for the regex to scan.

```python
@input_guardrail
async def misrepresentation_guardrail(ctx, agent, agent_input) -> GuardrailFunctionOutput:
    reason = find_misrepresentation_request(_as_text(agent_input))
    return GuardrailFunctionOutput(output_info=reason, tripwire_triggered=reason is not None)
```
`@input_guardrail` registers this to run **before** the model is called.
`tripwire_triggered=True` makes the SDK raise `InputGuardrailTripwireTriggered`
instead of proceeding — so a bad message is stopped before any token is spent.
It's `async` because that's the interface the SDK expects, but it awaits
nothing, so it returns instantly.

## `lead_desk/agent.py` — wiring the agent to Gemini

```python
from openai import AsyncOpenAI
from agents import Agent, OpenAIChatCompletionsModel, set_tracing_disabled
load_dotenv()
```
`load_dotenv()` reads `.env` into environment variables so `GEMINI_API_KEY` is
available via `os.environ`.

```python
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
set_tracing_disabled(True)
```
The base URL is Gemini's **OpenAI-compatible** endpoint — this is the whole
trick that lets the OpenAI Agents SDK talk to Gemini. Tracing is off because
the SDK's default trace exporter wants an OpenAI key we don't have.

```python
def _build_model() -> OpenAIChatCompletionsModel:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key: raise RuntimeError(...)
    client = AsyncOpenAI(api_key=api_key, base_url=GEMINI_BASE_URL)
    model_name = os.environ.get("LEAD_DESK_MODEL", "gemini-3.6-flash")
    return OpenAIChatCompletionsModel(model=model_name, openai_client=client)
```
We fail loudly if the key is missing. We build an `AsyncOpenAI` client but
point it at Google. **Why `OpenAIChatCompletionsModel` and not a bare model
string:** a bare string would make the SDK use OpenAI's own client/base URL; we
must inject our Gemini-pointed client, so we wrap it. Default model is
`gemini-3.6-flash` because the paper's `gemini-2.5-flash` now 404s (see
CORRECTIONS.md).

```python
INSTRUCTIONS = """You are Lead Desk ... call lookup_rate_card ... You classify
only — you do not decide whether the lead gets saved."""
```
The system prompt. It tells the model to call the tools before talking money,
to be skeptical (so red flags get raised), and — crucially — that it does not
decide saving. Note what's absent: no rate, no hours, no minimum price.

```python
def build_agent() -> Agent[FreelancerProfile]:
    return Agent[FreelancerProfile](name="Lead Desk", instructions=INSTRUCTIONS,
        model=_build_model(),
        tools=[lookup_rate_card, check_availability, send_proposal],
        input_guardrails=[misrepresentation_guardrail],
        output_type=LeadTriage)
```
`Agent[FreelancerProfile]` ties the context type to the agent so the tools'
`ctx.context` is typed. `output_type=LeadTriage` is what forces structured
output — the SDK turns the model's reply into a validated `LeadTriage` instead
of a paragraph. All three tools are listed; `send_proposal`'s gate hides it
when unverified.

## `lead_desk/decision.py` — Python owns the save call

```python
def should_save(triage: LeadTriage) -> bool:
    return triage.priority == "high"
```
The entire Task 3 save rule, in Python, reading the typed field. If the model
called a save tool instead, the task scores zero — so the decision lives here.

## `lead_desk/data_store.py` — file I/O

```python
ROOT = Path(__file__).resolve().parent.parent
LEADS_FILE = ROOT / "leads.json"
SAVED_FILE = ROOT / "saved.json"
```
`__file__` is this file's path; `.resolve().parent.parent` walks up from
`lead_desk/data_store.py` to the project root, so paths work no matter where
you run from.

```python
def read_leads() -> list[dict]:
    return json.loads(LEADS_FILE.read_text(encoding="utf-8"))
```
Loads the six fixtures.

```python
def save_lead(record: dict) -> None:
    saved = []
    if SAVED_FILE.exists():
        try: saved = json.loads(SAVED_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError: saved = []
    saved.append(record)
    SAVED_FILE.write_text(json.dumps(saved, indent=2), encoding="utf-8")
```
Read-append-write so `saved.json` stays a growing JSON array. The `try/except`
means a corrupt/empty file doesn't crash the run — we start a fresh list.

## `lead_desk/cli.py` — the entry point and pipeline

```python
import asyncio, json, sys
from agents import InputGuardrailTripwireTriggered, RunContextWrapper, Runner
```
`Runner` executes an agent; the exception is what a tripped guardrail raises.

```python
console = Console()
HARDCODED_MESSAGE = "Hi! We need a FastAPI backend ... 400000 PKR ..."
```
`rich` console for pretty output; the Task 0 hardcoded message used when no arg
is given.

```python
def _print_schema() -> None:
    schema = lookup_rate_card.params_json_schema
    console.print(Panel(json.dumps(schema, indent=2), ...))
```
Task 2 evidence command: prints the model-visible schema, which contains only
`skill` — proof the `ctx` param is stripped.

```python
def _print_triage(triage: LeadTriage) -> None:
```
Renders the verdict as a table. `f"{triage.budget_pkr:,}"` formats the integer
with thousands separators — and only works because it's a real number.

```python
async def _demo_conditional_tools() -> None:
    for verified in (False, True):
        profile = build_profile(); profile.verified = verified
        ctx = RunContextWrapper(context=profile)
        tools = await agent.get_all_tools(ctx)
        names = [t.name for t in tools]
```
Task 5B evidence. `get_all_tools` resolves each tool's `is_enabled` gate
exactly as the runner does, so the printed list proves `send_proposal` is
absent when unverified and present when verified — no API call needed.

```python
async def triage_one(message: str) -> None:
    profile = build_profile()
    agent = build_agent()
    try:
        result = await Runner.run(agent, message, context=profile)
    except InputGuardrailTripwireTriggered:
        console.print(Panel(REFUSAL_REASON, ...)); return
```
The heart of the pipeline. `Runner.run(...)` is the **async** call (Task 0):
it runs the guardrail, then the model, then tool calls, then structured output.
`context=profile` is how the private profile reaches the tools. If the
guardrail trips, we catch the exception and decline cleanly — an *uncaught*
exception would be a crash, not a refusal (Task 4 acceptance).

```python
    triage: LeadTriage = result.final_output
    _print_triage(triage)
    if should_save(triage):
        budget = triage.budget_pkr if triage.budget_pkr is not None else "n/a"
        console.print(f"[SAVE] priority={triage.priority} budget_pkr={budget}")
        record = triage.model_dump(); record["original_message"] = message
        save_lead(record)
    else:
        console.print(f"[SKIP] priority={triage.priority} — not saved.")
```
`result.final_output` is a `LeadTriage` instance (not a string). Python — not
the model — checks `should_save`, prints the one-line banner, and saves only
high-priority leads. `model_dump()` turns the pydantic object into a plain dict
for JSON.

```python
async def _amain(argv):
    if argv and argv[0] == "--schema": _print_schema(); return
    if argv and argv[0] == "--conditional-tools": await _demo_conditional_tools(); return
    if argv and argv[0] == "--all":
        for lead in read_leads(): ... await triage_one(lead["message"])
        return
    message = " ".join(argv) if argv else HARDCODED_MESSAGE
    await triage_one(message)

def main() -> None:
    asyncio.run(_amain(sys.argv[1:]))
```
Argument routing. `main()` is the sync entry point registered in
`pyproject.toml` (`lead-desk = "lead_desk.cli:main"`); `asyncio.run(...)` starts
the event loop and drives the async pipeline — this is the "asynchronous
runner" the spec requires.

---

# Part B — Step by step, what happens on a run

Command: `uv run lead-desk "We need a FastAPI backend, budget 400000 PKR"`

1. **uv** resolves the `lead-desk` script → calls `cli.main()`.
2. `main()` calls `asyncio.run(_amain(argv))` — the event loop starts (async).
3. `_amain` sees a plain message (no flag) → calls `triage_one(message)`.
4. `triage_one` builds the **private profile** and the **agent**
   (`build_agent()` also builds the Gemini-pointed model).
5. `Runner.run(agent, message, context=profile)` executes:
   a. **Input guardrail** runs first (pure regex, no API call). If the message
      asks you to misrepresent yourself → tripwire → exception → we print a
      polite decline and stop. **Zero tokens spent.**
   b. Otherwise the **model** is called with the system prompt + the message +
      the tool schemas (rate card, availability, and — only if verified —
      send_proposal). The private profile is **not** in this payload.
   c. The model decides to **call tools**: `lookup_rate_card("fastapi")` and
      `check_availability("next week")`. The SDK runs those Python functions,
      which read `ctx.context` (the profile) and return small dicts.
   d. The model gets the tool results and produces a final answer **shaped as
      `LeadTriage`** (SDK validates it against the schema).
6. `result.final_output` is a `LeadTriage` object. We print it.
7. **Python decides**: `should_save(triage)` → `priority == "high"`.
   - High → print `[SAVE] priority=high budget_pkr=400000`, append to
     `saved.json`.
   - Otherwise → print `[SKIP]`, save nothing.
8. The event loop ends; the process exits cleanly.

### The five things the assignment is really testing (say these in the demo)
- **Async runner** — `asyncio.run` + `await Runner.run` (Task 0).
- **Private data** — the rate/hours live in `FreelancerProfile`, passed as
  context; the model only ever sees tool return values (Task 2).
- **Typed output** — `output_type=LeadTriage`, so the program branches on
  fields, not prose (Task 3).
- **Decision in Python** — `should_save()`, not a model-called tool (Task 3).
- **Refuse for free** — a regex input guardrail that spends no tokens (Task 4).
```

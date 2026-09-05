# Lead Desk

Takes one raw freelance client message and turns it into a typed, actionable
verdict — intent, budget, red flags, priority, and a suggested reply — so you
can act fast without reading the whole thing first.

## How it fits together

```
message
   │
   ▼
guardrail.py  ── input guardrail: misrepresentation request?
   │              ──► trips tripwire, 0 API calls, CLI declines cleanly
   │ no
   ▼
agent.py      ── Gemini agent (gemini-3.6-flash; spec's 2.5-flash is 404'd by
   │              Google now). Calls lookup_rate_card(skill)
   │              and check_availability(week), returns a typed LeadTriage.
   ▼
decision.py   ── plain Python: should_save() reads triage.priority
   │              (save only when priority == "high")
   ▼
data_store.py ── if high: print banner, append to saved.json
```

### Where the private data lives

The freelancer's numbers (minimum rate in PKR, skills, free hours) live in
**`lead_desk/profile.py`** as a `FreelancerProfile`, handed to the run *as
context*. The tools read from that context; the model only ever sees what a
tool returns. The minimum rate is in no instruction and no message — prove it
with `grep -r min_rate_pkr_hour lead_desk` (only profile.py matches), and see
the model-visible tool schema (no `ctx` param) with `uv run lead-desk --schema`.

### Files

- **`lead_desk/profile.py`** — `FreelancerProfile` (private context).
- **`lead_desk/tools.py`** — `lookup_rate_card` / `check_availability`, both
  read from run context.
- **`lead_desk/models.py`** — `LeadTriage`, the one typed output shape.
- **`lead_desk/agent.py`** — the agent, its tools, and the input guardrail.
- **`lead_desk/guardrail.py`** — zero-cost regex input guardrail.
- **`lead_desk/decision.py`** — `should_save()`: the save decision, in Python.
- **`lead_desk/data_store.py`** — reads `leads.json`, appends `saved.json`.
- **`leads.json`** — six sample client messages (input fixtures).
- **`saved.json`** — high-priority leads that cleared the bar (output).

## Setup

```bash
uv venv
uv sync
cp .env.example .env           # then paste in your GEMINI_API_KEY
```

## Run it

```bash
uv run lead-desk                       # one hardcoded message
uv run lead-desk "your message here"   # triage a specific message
uv run lead-desk --all                 # triage all six fixtures in leads.json
uv run lead-desk --schema              # print a tool's JSON schema (evidence)
```

## Test the parts that don't need an API key

```bash
uv run python -m pytest tests/test_guardrail.py -v   # (pytest optional)
```

The guardrail tests make no network calls and need no API key — proving the
refusal path really is free.

# Lead Desk

Takes one raw freelance client message and turns it into a typed, actionable
verdict: what they want, what they'll pay, whether it's worth your time —
without you having to read the whole thing first.

## How it fits together

```
message
   │
   ▼
guardrail.py  ── misrepresentation request? ──► refuse, 0 API calls, stop here
   │ no
   ▼
agent.py      ── Gemini agent, calls get_my_rate() / get_my_availability()
   │              tools, returns a typed LeadVerdict (never a paragraph)
   ▼
decision.py   ── plain Python: compares verdict to rate card + availability,
   │              decides worth_pursuing — the model never sets this itself
   ▼
data_store.py ── only if worth_pursuing: append to data/leads.json
```

- **`lead_desk/models.py`** — `LeadVerdict` (what the model returns) and
  `LeadDecision` (what Python computes afterwards). Kept separate on
  purpose: the model classifies, Python decides.
- **`lead_desk/tools.py`** — `get_my_rate` / `get_my_availability`. These
  are the *only* way the agent learns your rate or your calendar; the raw
  JSON files are never in its prompt.
- **`lead_desk/guardrail.py`** — a plain regex check for "pretend you have
  X years experience" / "don't mention you're new" style requests. Runs
  before the agent is ever invoked, so a matching message never reaches
  the API.
- **`lead_desk/decision.py`** — the actual "is this worth my time" logic.
  Reads the rate card and availability itself (independent of whatever the
  model said) and applies rules to `worth_pursuing`.
- **`data/rates.json`**, **`data/availability.json`** — stand in for
  wherever this data would really live (a database, a calendar API). Edit
  these to change your rate or free time.
- **`data/leads.json`** — created on first save; append-only log of leads
  that cleared the bar.

## Setup

```bash
uv venv
source .venv/bin/activate      # or `.venv\Scripts\activate` on Windows
uv pip install -e .
cp .env.example .env           # then paste in your GEMINI_API_KEY
```

## Run it

```bash
uv run lead-desk "We need a FastAPI backend, 3-4 weeks, budget around $4,000. Can you start next week?"
```

or pipe a message in:

```bash
echo "quick job should take an hour, no budget mentioned" | uv run lead-desk
```

Output is JSON on stdout — either a refusal object (guardrail fired) or a
full `LeadDecision`.

## Test the parts that don't need an API key

```bash
uv run pytest tests/test_guardrail.py -v
```

`tests/sample_messages.py` has a few hand-written messages (a real lead, a
vague no-budget one, a revenue-share pitch, a lowball-with-pressure one,
and a misrepresentation request) to run through the CLI by hand and sanity
check each branch.

## Adjusting the rules

`decision.py`'s thresholds (minimum budget, what counts as "too many soft
red flags", how availability is checked) are plain Python — read them,
they're short — and are the first thing worth changing if your own bar for
"worth pursuing" differs from what's encoded here.

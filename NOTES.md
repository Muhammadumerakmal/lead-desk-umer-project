# NOTES

One line per task: what came back wrong the first time, and what I changed.

- **Task 0** — The spec's `gemini-2.5-flash` now returns a 404 ("no longer available
  to new users, use gemini-3.6-flash"), so I kept 3.6-flash so the agent actually
  runs; also the entry point was synchronous (`Runner.run_sync`) — switched it to
  `Runner.run` under `asyncio.run` as the spec requires.
- **Task 1** — First tools were `get_my_rate()` / `get_my_availability()` with no
  arguments; renamed to `lookup_rate_card(skill)` / `check_availability(week)` and
  made the rate card return "no rate on file" for an unknown skill instead of a number.
- **Task 2** — Tools originally read the numbers from disk at module level; moved the
  private data into a `FreelancerProfile` passed as run context, and confirmed via
  `--schema` that the `ctx` parameter never appears in the model-visible schema.
- **Task 3** — Output was a `LeadVerdict` (USD, no priority) and the save decision was
  a tangle of `worth_pursuing` rules; replaced it with `LeadTriage` (PKR `budget_pkr`,
  `priority`, `suggested_reply`) and reduced the save rule to `priority == "high"` in
  Python, writing to `saved.json` after a one-line banner.
- **Task 4** — The refusal was a manual pre-check function, not an SDK guardrail; wrapped
  it as an `@input_guardrail` that trips the tripwire with no model call, and caught
  `InputGuardrailTripwireTriggered` in the CLI so it declines instead of crashing.
- **Task 5** — Chose B (conditional tools). First tried filtering the tools list by
  hand at build time; switched to the SDK's `is_enabled` gate on `send_proposal` so
  `get_all_tools` resolves it per-run, and proved via `--conditional-tools` that an
  unverified profile is never offered the tool while a verified one is.

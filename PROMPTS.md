# Prompts used to build Lead Desk

> **Read this first.** In the timed exam, this file must hold every prompt
> *you personally* sent to Claude Code, in order, grouped by task, verbatim.
> It is assessed, and a log reconstructed from memory reads as exactly that.
> What follows is a **reference design sequence** at the level of specificity
> worth aiming for — an example of *how* to prompt, not something to submit as
> your own. The paper disqualifies a finished project from any outside source,
> so record your real prompts as you go and replace this text with them.

---

## Task 0 — Project and connection

- "Set up a uv project called lead-desk, Python 3.13+, deps on openai-agents,
  pydantic, python-dotenv, rich. Add .env.example for GEMINI_API_KEY and
  git-ignore .env."
- "Wire agent.py to Gemini via its OpenAI-compatible endpoint
  (https://generativelanguage.googleapis.com/v1beta/openai/) using AsyncOpenAI
  + OpenAIChatCompletionsModel — not a bare model string. Read the model name
  from an env var. Disable tracing since we're not on OpenAI."
- "Make the entry point asynchronous: an async main run via asyncio.run that
  calls Runner.run (not run_sync) on one hardcoded client message and prints
  the result."

## Task 1 — Sample data and lookup tools

- "Create leads.json with six sample client messages, each with id, message,
  platform. Cover: well-budgeted, revenue-share-instead-of-pay, too-vague,
  urgent, very-small-job, aggressive-about-deadlines."
- "In tools.py add two @function_tool functions: lookup_rate_card(skill) that
  returns my hourly rate for that skill, and check_availability(week) that
  returns free hours that week. If a skill isn't one I offer, return no rate
  so the model has to say it doesn't know rather than invent a number. Write
  the docstrings for the model to pick the right tool."

## Task 2 — Data the model is never given

- "Define a FreelancerProfile (pydantic) with name, min_rate_pkr_hour, skills,
  hours_free_per_week, verified. Build it in code and pass it to the run as
  context. Change both tools to read from ctx.context instead of module-level
  data, so the minimum rate never appears in the prompt or any message."
- "Add a --schema command that prints lookup_rate_card's JSON schema so I can
  show the ctx parameter isn't in it. Explain why the SDK strips it."

## Task 3 — A verdict the program can act on

- "Replace the output type with LeadTriage: intent (short string), budget_pkr
  (int or absent), red_flags (list of strings), priority (high/medium/low),
  suggested_reply (string). Set it as output_type so the shape comes back
  reliably."
- "Add save_lead in data_store.py that appends a triage record to saved.json.
  Keep the save decision in Python — should_save() returns priority == 'high'.
  In the CLI, print a one-line banner with priority and budget, then save only
  when should_save is true. The model must not call save_lead itself."

## Task 4 — Refusing before you pay

- "Turn the misrepresentation check into a proper SDK @input_guardrail that
  makes no model call and trips the tripwire on 'pretend you have 10 years',
  'don't mention you're new', 'fake a portfolio' style messages. Catch
  InputGuardrailTripwireTriggered in the CLI and print a polite decline, exit
  cleanly. Keep the regex function pure so it's unit-testable without a key."

## Task 5 — Bonus B, conditional tools

- "Add send_proposal(client_message, proposed_rate_pkr) gated with
  is_enabled reading ctx.context.verified, so it's only offered when verified
  is True. Add a --conditional-tools command that resolves get_all_tools for
  an unverified and a verified profile and prints both tool lists as proof the
  model never sees send_proposal in the unverified case."

---

## Review / follow-up prompts (the kind worth sending yourself)

- "Why does OpenAIChatCompletionsModel need an explicit client instead of a
  bare model string here?"
- "gemini-2.5-flash returns a 404 saying it's no longer available — what does
  that mean and what should I use instead?"
- "Show me the diff before running it — I want to read every line."
- "Walk me through what happens when budget_pkr is null but the client clearly
  wants a full build."

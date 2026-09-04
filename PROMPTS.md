# Prompts used to build Lead Desk

In an actual timed exam, this file is meant to hold every prompt you
personally sent to Claude Code, in order, verbatim. Below is the design
sequence this reference implementation was actually built from — treat it
as an example of the *level of specificity* worth aiming for, not
something to copy-paste into your own submission (the paper explicitly
disqualifies a finished project from any outside source).

1. "Set up a uv project called lead-desk, Python 3.13, deps on
   openai-agents, pydantic, python-dotenv. Add a .env.example for
   GEMINI_API_KEY."

2. "Define two pydantic models in models.py: LeadVerdict, with intent
   (enum: new_project/quick_task/consultation/ongoing_role/vague/spam),
   one_line_summary, stated_budget_usd (nullable), estimated_hours
   (nullable), red_flags (list of enum), confidence (0-1). And
   LeadDecision, which wraps a LeadVerdict plus hourly_rate_usd,
   free_hours_this_week, worth_pursuing, reason, saved — this one gets
   built by our own code, not the model."

3. "Create data/rates.json and data/availability.json as the source of
   truth for my rate and free hours. Then in tools.py write two
   @function_tool-decorated functions, get_my_rate and get_my_availability,
   that read those files and return a small dict. The agent should never
   see the raw JSON in its prompt — only what these tools return."

4. "In guardrail.py write a pure-Python (no LLM call) check that catches
   messages asking me to misrepresent my experience — things like
   'pretend you have 10 years experience', 'don't mention you're new',
   'fake a portfolio'. It needs to run before the agent is invoked at all,
   so a matching message costs zero API calls. Regex is fine."

5. "Wire up agent.py: Gemini via its OpenAI-compatible endpoint
   (https://generativelanguage.googleapis.com/v1beta/openai/), using
   AsyncOpenAI + OpenAIChatCompletionsModel from the Agents SDK, not a
   bare model string. Disable tracing since we're not using OpenAI.
   output_type=LeadVerdict, tools=[get_my_rate, get_my_availability].
   Write instructions that tell it to classify only — no drafting replies,
   no deciding whether to pursue."

6. "Write decision.py: given a LeadVerdict, read the rate card and
   availability directly (don't trust the model's arithmetic), and decide
   worth_pursuing with explicit rules — budget below minimum, a
   disqualifying red flag, no free hours, or too many soft red flags at
   once should all be able to sink a lead on their own. Return a
   human-readable reason string alongside the bool."

7. "cli.py: take the message from argv or stdin, run the guardrail first
   and short-circuit on a hit, otherwise run the agent, evaluate the
   decision, and only append to leads.json if worth_pursuing is true.
   Print the result as JSON."

8. "Add a few sample messages covering a real lead, a vague no-budget one,
   a revenue-share pitch, a lowball-with-pressure one, and a
   misrepresentation attempt, and a pytest file that proves the
   guardrail catches the last one without needing an API key."

Follow-up prompts during review, the kind you should expect to send
yourself: "why does OpenAIChatCompletionsModel need an explicit client
instead of just a model string here?", "walk me through what happens if
stated_budget_usd is None but the client clearly wants a full site built",
"show me the diff, I want to read it before running it."

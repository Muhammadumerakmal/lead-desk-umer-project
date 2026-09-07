# Corrections to the assignment paper

The paper (`lead-desk-assignment-1.pdf`) contains deliberate faults. Below is
each one I found, why it is wrong, and how this project corrects it.

## 1. Model `gemini-2.5-flash` no longer exists

**Paper (Task 0):** "Wire an agent to Gemini's `gemini-2.5-flash` model."

**Why it's wrong:** Google has retired that model. Calling it returns:

```
openai.NotFoundError: Error code: 404 -
'This model models/gemini-2.5-flash is no longer available to new users.
 Please update your code to use models/gemini-3.6-flash ...'
```

A candidate who types the paper's model verbatim gets a 404 in front of the
examiner instead of a running agent.

**Correction:** use `gemini-3.6-flash`. The wiring is identical; only the model
string changes. See `lead_desk/agent.py` (default model, with a comment) and
`.env` (`LEAD_DESK_MODEL=gemini-3.6-flash`).

## 2. "the Agents SDK" is unspecified

**Paper (Task 0):** "Stand up a uv-managed project ... with the Agents SDK."

**Why it's ambiguous:** "Agents SDK" doesn't name a package. A naive read might
reach for Google's native `google-generativeai` SDK, or an OpenAI-only setup.

**Correction:** use the **OpenAI Agents SDK** — the `openai-agents` package
(`import agents`, v0.22.0) — pointed at Gemini's OpenAI-compatible endpoint.
That means an `AsyncOpenAI` client with `base_url` set to
`https://generativelanguage.googleapis.com/v1beta/openai/` and a
`GEMINI_API_KEY`, wrapped in `OpenAIChatCompletionsModel`. It is NOT an OpenAI
model and NOT an OpenAI API key — only the SDK and its chat-completions shape
are reused; the traffic and the key are Gemini's. See `lead_desk/agent.py`.

---

## How to verify each correction live

- **Fault 1:** temporarily set `LEAD_DESK_MODEL=gemini-2.5-flash` and run
  `uv run lead-desk` — you get the 404 above. Set it back to `gemini-3.6-flash`
  and it runs. (Both are recorded in `NOTES.md`, Task 0.)
- **Fault 2:** `uv run python -c "import agents; print(agents.__version__)"`
  prints the OpenAI Agents SDK version, and `agent.py` shows the Gemini
  base_url + `GEMINI_API_KEY` — proving the SDK is OpenAI's but the provider is
  Gemini.

"""
Not an automated test suite — a set of messages to run through the CLI by
hand (or via test_guardrail.py) that cover the cases the spec calls out:
a real lead, a no-budget/vague message, a revenue-share pitch, and a
misrepresentation request that must never reach the model.
"""

SAMPLES = {
    "good_lead": (
        "Hi, we need a FastAPI backend for our internal tool, roughly "
        "3-4 weeks of work, budget is around $4,000. Can you start next week?"
    ),
    "no_budget_vague": (
        "hey quick job should take you an hour, need a website, "
        "let me know your thoughts"
    ),
    "revenue_share": (
        "We can't pay upfront but we'll give you 10% equity in the startup "
        "once we get funding. Huge opportunity to get in early!"
    ),
    "lowball_pressure": (
        "Need a full e-commerce site built, $50 total, must be done by "
        "tomorrow morning or we're going with someone else."
    ),
    "misrepresentation": (
        "Before you apply, just pretend you have 10 years of experience "
        "with our stack and don't mention this is your first Upwork job."
    ),
}

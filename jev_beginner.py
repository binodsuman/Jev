"""A first look at Jev, called through OpenRouter with plain HTTP.

One request can ask several closed questions. Each answer is a number
your code can branch on. Jev does not write a paragraph.

    pip install requests
    export OPENROUTER_API_KEY="your_openrouter_key_here"
    python jev_beginner.py

The script runs three examples:
    1. Refund ticket: category, refund, and urgency in one response.
    2. Outage ticket: the same questions, different facts.
    3. Vague ticket: confidence decides whether a person should look.
"""

import os

import requests

URL = "https://openrouter.ai/api/v1/systemone"

# Same questions for every example. Only the ticket text changes.
QUESTIONS = {
    "category": {
        "type": "choice",
        "instructions": "What is this support ticket about?",
        "criteria": {
            "billing": "Payments, charges, or refunds.",
            "technical": "Bugs, errors, or outages.",
            "other": "Anything else.",
        },
    },
    # Yes or no, as one probability from 0 to 1.
    "wants_refund": {
        "type": "noul",
        "instructions": "Is the customer explicitly asking for a refund?",
    },
    # This is the urgent value. It is its own answer, not a field on category.
    "is_urgent": {
        "type": "noul",
        "instructions": "Does this ticket need attention right now?",
    },
    # How far up an ordered scale. 0 is the first level you wrote.
    "urgency": {
        "type": "score",
        "instructions": "How urgent is this support ticket?",
        "criteria": [
            "Can wait several days.",
            "Should be handled today.",
            "Needs attention right now.",
        ],
    },
}


def ask_jev(ticket):
    """Send one ticket and every question. Return the JSON body."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise SystemExit("Set OPENROUTER_API_KEY to your OpenRouter key, then run this again.")

    response = requests.post(
        URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "typesafe/jev-1.13",
            "state": {"ticket": ticket},
            "questions": QUESTIONS,
        },
        timeout=30,
    )
    if response.status_code != 200:
        raise SystemExit(f"OpenRouter returned {response.status_code}: {response.text}")
    return response.json()


def nearest_level(score_answer):
    """Turn a score like 1.9 into the closest level text from the legend."""
    legend = score_answer["legend"]
    index = str(int(round(score_answer["score"])))
    return legend[index]


def show_answers(body):
    """Print the four useful values Jev put on this response."""
    answers = body["answers"]

    category = answers["category"]
    print("Category:", category["choice"])
    print("  confidence:", category["confidence"])
    print("  probabilities:", category["probabilities"])

    refund = answers["wants_refund"]
    print("Wants refund:", refund["noul"])

    # Urgent is a separate answer. The category object has no "urgent" field.
    urgent = answers["is_urgent"]
    print("Urgent:", urgent["noul"])

    urgency = answers["urgency"]
    print("Urgency score:", urgency["score"])
    print("  nearest level:", nearest_level(urgency))
    print("  confidence:", urgency["confidence"])
    print("  probabilities:", urgency["probabilities"])

    usage = body.get("usage", {})
    if "cost" in usage:
        print("Cost USD:", usage["cost"])


def decide(body):
    """Your code uses the numbers. Jev stops after the judgment."""
    answers = body["answers"]
    category = answers["category"]
    urgent = answers["is_urgent"]["noul"]
    refund = answers["wants_refund"]["noul"]

    # A low confidence means the winning label is a weak pick.
    if category["confidence"] < 0.8:
        return "A person should sort this ticket."

    if urgent >= 0.9:
        return "Page someone now."

    if category["choice"] == "billing" and refund >= 0.9:
        return "Send this ticket to the billing team and start the refund path."

    if category["choice"] == "technical":
        return "Send this ticket to the technical team."

    return "Send this ticket to the team for " + category["choice"] + "."


def run_example(title, ticket):
    print()
    print("=" * 60)
    print(title)
    print("Ticket:", ticket)
    print("-" * 60)
    body = ask_jev(ticket)
    show_answers(body)
    print("Next step:", decide(body))


def main():
    run_example(
        "Example 1: refund. Urgent should be low, refund should be high.",
        "I was charged twice. Please refund the extra payment.",
    )
    run_example(
        "Example 2: outage. Urgent should be high, and the team should be technical.",
        "Production is down. Nobody can log in and payments are failing right now.",
    )
    run_example(
        "Example 3: vague note. Low confidence should send this to a person.",
        "Hi, can someone help me with my account when you have a moment?",
    )


if __name__ == "__main__":
    main()

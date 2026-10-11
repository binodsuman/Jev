OPENROUTER_API_KEY = ""  # Paste your OpenRouter key here.

import requests

ticket = "I was charged twice. Please refund the extra payment."

response = requests.post(
    "https://openrouter.ai/api/v1/systemone",
    headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
    json={
        "model": "typesafe/jev-1.13",
        "state": {"ticket": ticket},
        "questions": {
            "category": {
                "type": "choice",
                "instructions": "What is this support ticket about?",
                "criteria": {
                    "billing": "Payments, charges, or refunds.",
                    "technical": "Bugs, errors, or outages.",
                    "other": "Anything else.",
                },
            },
        },
    },
)

print(response.json()["answers"]["category"]["choice"])

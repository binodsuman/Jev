OPENROUTER_API_KEY = ""  # Paste your key here. Leave this empty to use the export below.

import os
import requests

ticket = "I was charged twice. Please refund the extra payment."

response = requests.post(
    "https://openrouter.ai/api/v1/systemone",
    headers={
        "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}",
        "Content-Type": "application/json",
    },
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
    timeout=30,
)

print(response.json()["answers"]["category"]["choice"])
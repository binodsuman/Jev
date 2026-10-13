"""Send the user text and the two questions to Jev."""

import requests

from config import JEV_MODEL, JEV_URL, OPENROUTER_API_KEY
from questions import QUESTIONS


# Ask Jev to classify one user request.
# Returns the JSON body: answers["task"], answers["complexity"], and usage.
# Gives up after 12 seconds. router.py catches that timeout.
def ask_jev(user_request):
    response = requests.post(
        JEV_URL,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": JEV_MODEL,
            # state is the text Jev judges. The questions stay the same every call.
            "state": {"request": user_request},
            "questions": QUESTIONS,
        },
        timeout=12,
    )
    response.raise_for_status()
    return response.json()

"""Ask the Gemini model that policy.py selected."""

import time

import requests

from config import CHAT_URL, OPENROUTER_API_KEY


# Send the same user sentence to one Gemini model and return three things:
# the answer text, the usage object (tokens and cost), and the latency in milliseconds.
# Gives up after 45 seconds. router.py retries on Flash if Flash-Lite fails.
def ask_gemini(model, user_request):
    started = time.perf_counter()
    response = requests.post(
        CHAT_URL,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": user_request}],
            # Keep the on-screen answer short.
            "max_tokens": 400,
            # Ask OpenRouter to include the dollar cost in usage.
            "usage": {"include": True},
        },
        timeout=45,
    )
    response.raise_for_status()
    body = response.json()
    elapsed_ms = (time.perf_counter() - started) * 1000
    text = body["choices"][0]["message"]["content"].strip()
    return text, body.get("usage", {}), elapsed_ms

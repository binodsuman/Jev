"""Call Jev, apply the route, then call Gemini or refuse."""

import time

import requests

from config import CAPABLE_MODEL, FAST_MODEL
from gemini_client import ask_gemini
from jev_client import ask_jev
from policy import decide

# Shown when the route is "refuse". Gemini is not called.
REFUSAL = (
    "This app answers questions, coding tasks, and reasoning problems. "
    "It does not take actions, create images, or look up private data."
)


# Run one user request from start to finish.
# Returns a dictionary that main.py prints: route, answer, timings, and cost.
def route_request(user_request):
    fallback = None
    answers = None
    jev_usage = {}
    jev_ms = None

    try:
        started = time.perf_counter()
        body = ask_jev(user_request)
        jev_ms = (time.perf_counter() - started) * 1000
        answers = body["answers"]
        jev_usage = body.get("usage", {})
        route, reason = decide(answers)
    except requests.Timeout:
        # Jev did not answer in time. Use the stronger model instead of guessing "simple".
        route, reason = "capable", "Jev timed out"
        fallback = "used Gemini Flash because Jev timed out"

    # Unsupported requests stop here. No Gemini call, no extra cost.
    if route == "refuse":
        return _pack(user_request, route, reason, None, REFUSAL, fallback, answers, jev_usage, jev_ms, {}, None)

    model = FAST_MODEL if route == "fast" else CAPABLE_MODEL
    try:
        answer, llm_usage, llm_ms = ask_gemini(model, user_request)
    except (requests.Timeout, requests.HTTPError):
        # Flash-Lite failed. Try Flash once. If Flash itself fails, let the error show.
        if model != FAST_MODEL:
            raise
        answer, llm_usage, llm_ms = ask_gemini(CAPABLE_MODEL, user_request)
        model = CAPABLE_MODEL
        route = "capable"
        fallback = "used Gemini Flash because Flash-Lite failed"

    return _pack(
        user_request, route, reason, model, answer, fallback,
        answers, jev_usage, jev_ms, llm_usage, llm_ms,
    )


# Put the pieces into one dictionary so main.py can print them without knowing the API shapes.
def _pack(user_request, route, reason, model, answer, fallback, answers, jev_usage, jev_ms, llm_usage, llm_ms):
    task = answers["task"] if answers else {}
    complexity = answers["complexity"] if answers else {}
    return {
        "request": user_request,
        "route": route,
        "reason": reason,
        "model": model,
        "answer": answer,
        "fallback": fallback,
        "choice": task.get("choice"),
        "confidence": task.get("confidence"),
        "probabilities": task.get("probabilities") or {},
        "score": complexity.get("score"),
        "jev_usage": jev_usage,
        "jev_ms": jev_ms,
        "llm_usage": llm_usage,
        "llm_ms": llm_ms,
    }

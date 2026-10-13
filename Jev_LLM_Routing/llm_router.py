"""Same demo as main.py, but a normal chat model picks the route instead of Jev.

Before Jev, most apps did this: send the user text to a cheap LLM, ask it to
reply with a label, parse that text, then call the model the label points at.
The labels, the score scale, the policy, the examples, and the Gemini answer
call are the same as the Jev demo. Only the router call is different.

    python llm_router.py
    python llm_router.py "Write a Python palindrome function."
    python llm_router.py demo

Compare the "Router LLM" cost line with the "Jev" cost line from main.py.
"""

import json
import sys
import time

import requests

from config import CAPABLE_MODEL, CHAT_URL, FAST_MODEL, OPENROUTER_API_KEY
from gemini_client import ask_gemini
from main import EXAMPLES
from policy import decide
from questions import QUESTIONS
from router import REFUSAL

# Industry default: a small, cheap chat model does the classification.
ROUTER_MODEL = FAST_MODEL


# Fixed instructions. This does not change from one user request to the next.
# The model is told to classify, not to answer, and to use only these four labels.
def build_system_prompt():
    task = QUESTIONS["task"]
    complexity = QUESTIONS["complexity"]
    lines = [
        "You are a router. Do not answer the user's request.",
        task["instructions"],
        "choice must be exactly one of these labels:",
    ]
    for name, text in task["criteria"].items():
        lines.append(f"- {name}: {text}")
    lines.append(complexity["instructions"] + " score is a number from 0 (easy) to 2 (hard).")
    for index, text in enumerate(complexity["criteria"]):
        lines.append(f"- {index}: {text}")
    lines.append(
        "Reply with one JSON object and no other text.\n"
        '{"choice":"simple","confidence":0.9,'
        '"probabilities":{"simple":0.9,"coding":0.0,"reasoning":0.0,"unsupported":0.0},'
        '"score":0.2}'
    )
    return "\n".join(lines)


SYSTEM_PROMPT = build_system_prompt()


# The only part that changes per call: the request we want classified.
def request_prompt(user_request):
    return "Classify this request:\n" + user_request


# Ask the router LLM to classify. Returns the raw text, usage, and latency.
# The reply is still text. parse_router_text() has to pull JSON out of it.
# Jev returns numbers your code can read directly, with no prompt and no parse.
def ask_router_llm(user_request):
    started = time.perf_counter()
    response = requests.post(
        CHAT_URL,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": ROUTER_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": request_prompt(user_request)},
            ],
            # temperature 0 makes the wording more stable. It does not make it certain.
            "temperature": 0,
            "max_tokens": 180,
            "usage": {"include": True},
        },
        timeout=30,
    )
    response.raise_for_status()
    body = response.json()
    elapsed_ms = (time.perf_counter() - started) * 1000
    text = body["choices"][0]["message"]["content"].strip()
    return text, body.get("usage", {}), elapsed_ms


# Turn the router's text into the same answers shape that policy.decide() expects.
# Returns None when the text is not usable JSON. That is the usual failure mode.
def parse_router_text(text):
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        data = json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return None

    choice = str(data.get("choice", "")).strip().lower()
    if choice not in QUESTIONS["task"]["criteria"]:
        return None

    probabilities = data.get("probabilities")
    if not isinstance(probabilities, dict):
        probabilities = {name: 0.0 for name in QUESTIONS["task"]["criteria"]}
        probabilities[choice] = 1.0

    return {
        "task": {
            "choice": choice,
            "confidence": _number(data.get("confidence"), 1.0),
            "probabilities": probabilities,
        },
        "complexity": {
            "score": _number(data.get("score"), 1.0),
        },
    }


# Same path as router.route_request, with the router LLM in Jev's place.
def route_with_llm(user_request):
    fallback = None
    answers = None
    raw_text = ""
    router_usage = {}
    router_ms = None

    try:
        raw_text, router_usage, router_ms = ask_router_llm(user_request)
        answers = parse_router_text(raw_text)
        if answers is None:
            route, reason = "capable", "router text was not valid JSON"
            fallback = "used Gemini Flash because the router reply could not be parsed"
        else:
            route, reason = decide(answers)
    except requests.Timeout:
        route, reason = "capable", "router LLM timed out"
        fallback = "used Gemini Flash because the router timed out"

    if route == "refuse":
        result = _pack(user_request, route, reason, None, REFUSAL, fallback, answers, router_usage, router_ms, {}, None)
        result["raw_text"] = raw_text
        return result

    model = FAST_MODEL if route == "fast" else CAPABLE_MODEL
    try:
        answer, llm_usage, llm_ms = ask_gemini(model, user_request)
    except (requests.Timeout, requests.HTTPError):
        if model != FAST_MODEL:
            raise
        answer, llm_usage, llm_ms = ask_gemini(CAPABLE_MODEL, user_request)
        model = CAPABLE_MODEL
        route = "capable"
        fallback = "used Gemini Flash because Flash-Lite failed"

    result = _pack(
        user_request, route, reason, model, answer, fallback,
        answers, router_usage, router_ms, llm_usage, llm_ms,
    )
    result["raw_text"] = raw_text
    return result


# Same fields as the Jev report, plus the raw text the router model wrote.
def _pack(user_request, route, reason, model, answer, fallback, answers, router_usage, router_ms, llm_usage, llm_ms):
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
        "router_usage": router_usage,
        "router_ms": router_ms,
        "llm_usage": llm_usage,
        "llm_ms": llm_ms,
    }


# Print one result. The first cost line is what you compare with Jev.
def show(result):
    print("-" * 64)
    print("Request:", result["request"])
    print()
    print("Router LLM", ROUTER_MODEL)
    if result.get("raw_text"):
        print("  text        ", result["raw_text"].replace("\n", " ")[:220])
    print(f"  task         {result['choice']}")
    print(f"  confidence   {_num(result['confidence'])}")
    print(f"  probabilities  {_probabilities(result['probabilities'])}")
    print(f"  complexity   {_num(result['score'])}")
    print(f"  {_ms(result['router_ms'])}    {_usage(result['router_usage'])}")
    print()
    print(f"Route    {result['route']}")
    print(f"Reason   {result['reason']}")
    print(f"Model    {result['model'] or '-'}")
    if result["fallback"]:
        print(f"Fallback {result['fallback']}")
    print()
    print("Answer")
    for line in result["answer"].splitlines():
        print(" ", line)
    print()
    print(f"Gemini   {_ms(result['llm_ms'])}    {_usage(result['llm_usage'])}")
    router_cost = _dollars(result["router_usage"])
    answer_cost = _dollars(result["llm_usage"])
    total = None if router_cost is None and answer_cost is None else (router_cost or 0) + (answer_cost or 0)
    print(f"Bills    router {_money(router_cost)}    answer {_money(answer_cost)}    total {_money(total)}")
    print("-" * 64)
    print()
    return router_cost, answer_cost


def _probabilities(probabilities):
    if not probabilities:
        return "-"
    order = ["simple", "coding", "reasoning", "unsupported"]
    names = [name for name in order if name in probabilities]
    names += [name for name in probabilities if name not in names]
    parts = []
    for name in names:
        parts.append(f"{name} {_num(_number(probabilities[name], None))}")
    return " | ".join(parts)


def _usage(usage):
    if not usage:
        return "-"
    tokens_in = usage.get("prompt_tokens", usage.get("input_tokens", "-"))
    tokens_out = usage.get("completion_tokens", usage.get("output_tokens", "-"))
    return f"in {tokens_in}  out {tokens_out}  {_money(_dollars(usage))}"


def _dollars(usage):
    if not usage:
        return None
    cost = usage.get("cost")
    if cost is None:
        return None
    return float(cost)


def _money(cost):
    if cost is None:
        return "cost n/a"
    return f"${cost:.8f}"


def _ms(value):
    if value is None:
        return "-"
    return f"{value:.0f} ms"


def _num(value):
    if value is None:
        return "-"
    return f"{float(value):.2f}"


def _number(value, default):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def main():
    if not OPENROUTER_API_KEY.strip():
        raise SystemExit("Paste your OpenRouter key on the first line of config.py")

    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        questions = EXAMPLES
    elif len(sys.argv) > 1:
        questions = [" ".join(sys.argv[1:])]
    else:
        questions = [EXAMPLES[0]]

    router_total = 0.0
    answer_total = 0.0
    for question in questions:
        router_cost, answer_cost = show(route_with_llm(question))
        router_total += router_cost or 0
        answer_total += answer_cost or 0

    if len(questions) > 1:
        print("=" * 64)
        print(f"Router LLM total   {_money(router_total)}    compare this with the Jev lines from main.py")
        print(f"Gemini answer total {_money(answer_total)}")
        print(f"Grand total        {_money(router_total + answer_total)}")


if __name__ == "__main__":
    main()

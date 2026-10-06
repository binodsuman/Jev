import os
import time
import statistics
import requests

API_KEY = os.environ["OPENROUTER_API_KEY"]

# --------------------------------------------------
# Configuration
# --------------------------------------------------

RUNS = 20

LLM_MODEL = "openai/gpt-5.6-luna"
JEV_MODEL = "typesafe/jev-1.13"

QUESTION = """
A customer says:
"I was charged twice for the same order. Please refund the duplicate payment."

Classify this request as exactly one of:
- billing
- technical
- general

Return only the category.
""".strip()


# --------------------------------------------------
# Normal LLM
# --------------------------------------------------

def call_llm():
    start = time.perf_counter()

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": LLM_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": QUESTION
                }
            ],
            "temperature": 0,
            "max_tokens": 20,
        },
        timeout=60,
    )

    elapsed = time.perf_counter() - start

    response.raise_for_status()

    data = response.json()

    answer = data["choices"][0]["message"]["content"]

    return elapsed, answer


# --------------------------------------------------
# Jev
# --------------------------------------------------

def call_jev():
    start = time.perf_counter()

    response = requests.post(
        "https://openrouter.ai/api/alpha/decisions",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": JEV_MODEL,

            "state": QUESTION,

            "questions": {
                "category": {
                    "type": "choice",

                    "instructions": (
                        "Which category best describes "
                        "the customer request?"
                    ),

                    "criteria": {
                        "billing": "Payments, charges and refunds",
                        "technical": "Bugs, APIs and technical problems",
                        "general": "Other customer requests",
                    },
                }
            },
        },
        timeout=60,
    )

    elapsed = time.perf_counter() - start

    response.raise_for_status()

    data = response.json()

    answer = data["answers"]["category"]["choice"]

    return elapsed, answer


# --------------------------------------------------
# Statistics
# --------------------------------------------------

def print_stats(name, times):

    average = statistics.mean(times)
    p50 = statistics.median(times)

    # statistics.quantiles uses n=100 for percentile calculation
    p95 = statistics.quantiles(
        times,
        n=100,
        method="inclusive"
    )[94]

    print(f"\n{name}")
    print("-" * 40)
    print(f"Average : {average * 1000:.0f} ms")
    print(f"P50     : {p50 * 1000:.0f} ms")
    print(f"P95     : {p95 * 1000:.0f} ms")


# --------------------------------------------------
# Main benchmark
# --------------------------------------------------

def main():

    print("\nJev vs Normal LLM")
    print("=" * 50)

    print(f"Runs      : {RUNS}")
    print(f"LLM       : {LLM_MODEL}")
    print(f"Jev       : {JEV_MODEL}")

    llm_times = []
    jev_times = []

    print("\nRunning benchmark...\n")

    for i in range(RUNS):

        # -----------------------------
        # LLM
        # -----------------------------

        try:
            latency, answer = call_llm()

            llm_times.append(latency)

            print(
                f"{i + 1:02d}  "
                f"LLM  {latency * 1000:7.0f} ms  "
                f"{answer.strip()}"
            )

        except Exception as e:
            print(f"{i + 1:02d}  LLM ERROR: {e}")


        # -----------------------------
        # Jev
        # -----------------------------

        try:
            latency, answer = call_jev()

            jev_times.append(latency)

            print(
                f"{i + 1:02d}  "
                f"Jev  {latency * 1000:7.0f} ms  "
                f"{answer}"
            )

        except Exception as e:
            print(f"{i + 1:02d}  Jev ERROR: {e}")


    # -----------------------------
    # Results
    # -----------------------------

    print("\n")
    print("=" * 50)
    print("BENCHMARK RESULTS")
    print("=" * 50)

    if llm_times:
        print_stats("Normal LLM", llm_times)

    if jev_times:
        print_stats("Jev", jev_times)


if __name__ == "__main__":
    main()
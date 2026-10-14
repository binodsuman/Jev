"""Start here. Gemini answers each exam question, then Jev grades that answer.

    python main.py
    python main.py 2
"""

import sys

from config import OPENROUTER_API_KEY
from judge import judge_case
from question import CASES


# Print one finished case: the exam, Gemini's answer, and Jev's grade.
def show(result):
    print("-" * 64)
    print("Question:", result["question"])
    print("Golden:  ", result["golden_answer"])
    print()
    print("Gemini")
    print(" ", result["llm_answer"])
    print()
    print("Jev")
    print("  verdict       ", result["choice"])
    print("  confidence    ", f"{result['confidence']:.2f}")
    print("  probabilities ", _probabilities(result["probabilities"]))
    print("  closeness     ", f"{result['score']:.2f}")
    print()
    print("Result", result["result"])
    print("Reason", result["reason"])
    print("-" * 64)
    print()


# Turn match / partial / wrong into one readable line.
def _probabilities(probabilities):
    order = ["match", "partial", "wrong"]
    return " | ".join(f"{name} {probabilities[name]:.2f}" for name in order)


# Check the key, then grade every case, or just the case number you pass.
def main():
    if not OPENROUTER_API_KEY.strip():
        raise SystemExit("Paste your OpenRouter key on the first line of config.py")

    # python main.py runs all three. python main.py 2 runs case 2 only.
    if len(sys.argv) > 1:
        cases = [CASES[int(sys.argv[1]) - 1]]
    else:
        cases = CASES

    for case in cases:
        show(judge_case(case))


if __name__ == "__main__":
    main()

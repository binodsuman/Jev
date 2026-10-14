"""Read Jev's verdict and name it correct, partial, or wrong.

The grading rules live in question.py. This file only reads the label Jev picked.
"""


# Look at the verdict choice. Returns the result word and a short reason.
# closeness is printed by main.py. It is not a second rule.
def decide(answers):
    verdict = answers["verdict"]["choice"]

    if verdict == "match":
        return "correct", "same fact or same number as the golden answer"

    if verdict == "partial":
        return "partial", "right topic, but not the golden answer"

    return "wrong", "different fact or a different number"

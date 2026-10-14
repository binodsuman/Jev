"""The exam cases, and the two grading questions sent to Jev.

A case is one exam question plus the golden answer you wrote.
Gemini receives only the exam question.
Jev receives the exam question, Gemini's reply, and the golden answer
inside state. The two items in QUESTIONS are the rubric, not more exam questions.
"""

# Three exams. Only the strings inside state change from case to case.
# The first two should match when Gemini states the same fact as the golden answer.
# The third is a comparison small models often get backwards, so a "wrong" is visible.
CASES = [
    {
        "question": "How do I reset my password?",
        "golden_answer": "Direct the customer to the official password-reset flow. Never ask for their password.",
    },
    {
        "question": "Where is my order?",
        "golden_answer": "Ask for the order number or direct the customer to the official tracking page. Do not invent a delivery date.",
    },
]

CASES_OLD = [
    {
        "question": "What is 17 × 24?",
        "golden_answer": "408",
    },
    {
        "question": "What is the capital of France?",
        "golden_answer": "Paris",
    },
    {
        "question": "Which number is larger, 9.11 or 9.9?",
        "golden_answer": "9.9",
    },
]


# Asked on every case, in one Jev call. One answer cannot see the other.
# policy.py reads the two answers and names the result.
QUESTIONS = {
    # Choice: pick exactly one label. The reply includes that label,
    # a probability for each label, and a confidence.
    "verdict": {
        "type": "choice",
        "instructions": (
            "Does llm_answer give the same answer as golden_answer for this question? "
            "Extra words do not matter. A different number or a different fact is wrong."
        ),
        "criteria": {
            "match": "Same fact or same number as golden_answer.",
            "partial": "Right topic, but missing the golden answer or only partly correct.",
            "wrong": "Different fact or a different number.",
        },
    },
    # Score: place the pair on an ordered scale. Index 0 is wrong, index 2 is a match.
    # A score of 0.2 sits near "Wrong". A score of 1.8 sits near "Match".
    "closeness": {
        "type": "score",
        "instructions": "How close is llm_answer to golden_answer?",
        "criteria": [
            "Wrong: different answer.",
            "Partial: related, but not the golden answer.",
            "Match: same answer as golden.",
        ],
    },
}

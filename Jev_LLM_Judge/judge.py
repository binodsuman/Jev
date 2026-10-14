"""Ask Gemini for an answer, then ask Jev if that answer matches the golden answer."""

import requests

from config import CHAT_URL, GEMINI_MODEL, JEV_MODEL, JEV_URL, OPENROUTER_API_KEY
from policy import decide
from question import QUESTIONS


# Send the exam question only. The golden answer stays out of this call,
# so Gemini cannot copy it. Returns the reply text.
def ask_gemini(question):
    response = requests.post(
        CHAT_URL,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": GEMINI_MODEL,
            "messages": [{"role": "user", "content": question}],
            # Keep the on-screen answer short.
            "max_tokens": 200,
        },
        timeout=45,
    )
    response.raise_for_status()
    body = response.json()
    return body["choices"][0]["message"]["content"].strip()


# Send the three texts as state, and the same two grading questions every time.
# Returns Jev's JSON body: answers["verdict"] and answers["closeness"].
def ask_jev(question, llm_answer, golden_answer):
    response = requests.post(
        JEV_URL,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": JEV_MODEL,
            "state": {
                "question": question,
                "llm_answer": llm_answer,
                "golden_answer": golden_answer,
            },
            "questions": QUESTIONS,
        },
        timeout=12,
    )
    response.raise_for_status()
    return response.json()


# Run one case from start to finish. Returns the dictionary main.py prints.
def judge_case(case):
    question = case["question"]
    golden_answer = case["golden_answer"]

    llm_answer = ask_gemini(question)
    body = ask_jev(question, llm_answer, golden_answer)
    answers = body["answers"]
    result, reason = decide(answers)

    return {
        "question": question,
        "golden_answer": golden_answer,
        "llm_answer": llm_answer,
        "result": result,
        "reason": reason,
        "choice": answers["verdict"]["choice"],
        "confidence": answers["verdict"]["confidence"],
        "probabilities": answers["verdict"]["probabilities"],
        "score": answers["closeness"]["score"],
    }

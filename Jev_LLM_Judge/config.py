# Settings for the whole demo. Every other file imports from here.

# Your OpenRouter key. It pays for the Gemini call and the Jev call.
OPENROUTER_API_KEY = ""  # Paste your OpenRouter key here.

# Writes llm_answer. This model sees the question only, never the golden answer.
GEMINI_MODEL = "google/gemini-3.1-flash-lite"

# Grades llm_answer against the golden answer. Jev does not write an answer.
JEV_MODEL = "typesafe/jev-1.13"

# Normal chat endpoint. Gemini uses this URL.
CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"

# Jev's decision API. This is not the chat endpoint.
JEV_URL = "https://openrouter.ai/api/alpha/decisions"

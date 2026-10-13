# Settings for the whole demo. Every other file imports from here.

# Your OpenRouter key. It pays for both the Jev call and the Gemini call.
OPENROUTER_API_KEY = ""  # Paste your OpenRouter key here.

# Jev classifies the request. It does not write the answer.
JEV_MODEL = "typesafe/jev-1.13"

# Cheap, fast model. Used only for a simple question Jev is sure about.
FAST_MODEL = "google/gemini-3.1-flash-lite"

# Stronger model. Used for coding, reasoning, hard questions, and fallbacks.
CAPABLE_MODEL = "google/gemini-3.8-flash"

# Jev's decision API. This is not the chat endpoint.
JEV_URL = "https://openrouter.ai/api/alpha/decisions"

# Normal chat endpoint. Gemini Flash-Lite and Gemini Flash both use this URL.
CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"

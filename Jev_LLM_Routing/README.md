# Jev LLM Routing

Jev classifies the request. This app sends it to Gemini Flash-Lite, Gemini Flash, or nowhere.

Paste your OpenRouter key on the first line of `config.py`.

```bash
pip install -r requirements.txt
python main.py "What is the capital of France?"
python main.py demo
```

`demo` runs six requests: a simple question, a coding task, a reasoning problem, an unsupported request, a vague sentence, and a "use the cheap model" override.

| File | What it does |
| --- | --- |
| `config.py` | API key and the three model names |
| `questions.py` | Choice question and score question |
| `jev_client.py` | Calls Jev |
| `policy.py` | fast, capable, or refuse |
| `gemini_client.py` | Calls Gemini |
| `router.py` | Timeout and one fallback |
| `main.py` | Prints the answer, route, latency, and cost |

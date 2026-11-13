"""Checks that the configured AI key works. Run from the project root:

    backend\\.venv\\Scripts\\python backend\\check_key.py

It makes two tiny requests and prints a verdict. The key itself is never printed.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app import llm  # noqa: E402
from app.config import load_settings  # noqa: E402

HINTS = {
    "auth": "The key is wrong, expired or revoked. Create a new key in Google AI Studio or the provider dashboard.",
    "permission": "The key is valid but not allowed to use this model or project. Ask who manages the key.",
    "model": "This model is not available to the key. Set the provider's model variable in backend/.env to a model your account allows.",
    "quota": "The account has no credit left, or the project's spend limit is reached. Check the provider's billing and usage limits.",
    "rate_limit": "Too many requests per minute for this key's usage tier. Wait a minute and run this again.",
    "network": "Could not reach the AI provider. The office network or proxy may be blocking its API.",
    "timeout": "The AI provider did not answer in time. Try again, or check the network.",
}

s = load_settings()
if not s.ai_enabled:
    print(f"NO KEY: {s.key_env_name} was not found. Put it in backend/.env and run this again.")
    sys.exit(1)

print(f"{s.provider_name} key found (length {len(s.api_key)}).")
failed = False

print(f"1. Chat model ({s.model}) ...", end=" ", flush=True)
try:
    text = llm.chat_text(s, "Reply with one word.", "Say: ok")
    print(f"WORKS (answered {text[:20]!r})")
except llm.AIUnavailable as e:
    failed = True
    print(f"FAILED [{e.code}]\n   {HINTS.get(e.code, e.message)}")

if s.embeddings_enabled:
    print(f"2. Embedding model ({s.embedding_model}) ...", end=" ", flush=True)
    try:
        vec = llm.embed(s, ["timeout error"])[0]
        print(f"WORKS ({len(vec)} numbers per text)")
    except llm.AIUnavailable as e:
        print(f"FAILED [{e.code}]\n   {HINTS.get(e.code, e.message)}\n"
              "   The portal still works: it falls back to keyword search instead of search by meaning.")
else:
    print("2. Embeddings: not enabled for this provider; using keyword search.")

sys.exit(2 if failed else 0)

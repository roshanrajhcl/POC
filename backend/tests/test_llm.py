from app import llm
from app.config import Settings


class RateLimitError(Exception):
    """Same name as the OpenAI error, so the wrapper treats it the same way."""
    def __init__(self, code=None):
        super().__init__("429")
        self.code = code


def test_no_credit_is_reported_as_quota_not_rate_limit():
    e = llm._wrap(RateLimitError(code="insufficient_quota"))
    assert e.code == "quota" and "credit" in e.message and "Billing" in e.message


def test_plain_rate_limit_stays_a_rate_limit():
    e = llm._wrap(RateLimitError(code="rate_limit_exceeded"))
    assert e.code == "rate_limit" and "too many requests" in e.message


def test_unknown_error_does_not_leak_details():
    e = llm._wrap(ValueError("secret detail sk-abc"))
    assert e.code == "error" and "sk-abc" not in e.message


def test_groq_uses_openai_compatible_endpoint_and_keyword_search(tmp_path):
    settings = Settings(ai_provider="groq", groq_api_key="gsk-test", data_dir=tmp_path)
    client = llm._client(settings)
    try:
        assert str(client.base_url).rstrip("/") == "https://api.groq.com/openai/v1"
        assert settings.model == "llama-3.3-70b-versatile"
        assert not settings.embeddings_enabled
    finally:
        client.close()


def test_gemini_uses_native_endpoint_and_keyword_search(tmp_path):
    settings = Settings(ai_provider="gemini", gemini_api_key="gemini-test", data_dir=tmp_path)
    assert settings.gemini_base_url == "https://generativelanguage.googleapis.com/v1beta"
    assert settings.model == "gemini-3.1-flash-lite"
    assert not settings.embeddings_enabled


def test_gemini_chat_json_uses_native_generate_content(monkeypatch, tmp_path):
    settings = Settings(ai_provider="gemini", gemini_api_key="gemini-test", data_dir=tmp_path)
    calls = []

    def generate(_settings, system, user, json_mode):
        calls.append((system, user, json_mode))
        return '{"ready": true}'

    monkeypatch.setattr(llm, "_gemini_generate", generate)
    assert llm.chat_json(settings, "system", "user") == {"ready": True}
    assert calls == [("system", "user", True)]

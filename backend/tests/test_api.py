import pytest
from fastapi.testclient import TestClient

from app import llm, main
from app.config import Settings
from app.rag.kb import KnowledgeBase
from conftest import Scripted, suggest


@pytest.fixture
def client(monkeypatch, keyless):
    monkeypatch.setattr(main, "settings", keyless)
    monkeypatch.setattr(main, "kb", KnowledgeBase(keyless))
    return TestClient(main.app)


@pytest.fixture
def keyed_client(monkeypatch, keyed):
    from conftest import fake_embed
    monkeypatch.setattr(main, "settings", keyed)
    monkeypatch.setattr(main, "kb", KnowledgeBase(keyed, embed_fn=fake_embed))
    return TestClient(main.app)


BODY = {"issue": "refresh_failed", "error": "Timeout error", "reports": ["NZ"]}


def test_health_without_key(client):
    body = client.get("/api/health").json()
    assert body["ai"] is False and body["model"] is None
    assert body["knowledge"]["documents"] >= 15 and body["knowledge"]["retrieval"] == "keyword"


def test_groq_health_reports_keyword_search(monkeypatch, tmp_path):
    settings = Settings(
        ai_provider="groq", groq_api_key="gsk-test", data_dir=tmp_path,
    )
    monkeypatch.setattr(main, "settings", settings)
    monkeypatch.setattr(main, "kb", KnowledgeBase(settings))
    body = TestClient(main.app).get("/api/health").json()
    assert body["ai"] is True and body["provider"] == "Groq"
    assert body["model"] == settings.model and body["embedding_model"] is None
    assert body["knowledge"]["retrieval"] == "keyword"


def test_gemini_health_reports_keyword_search(monkeypatch, tmp_path):
    settings = Settings(
        ai_provider="gemini", gemini_api_key="gemini-test", data_dir=tmp_path,
    )
    monkeypatch.setattr(main, "settings", settings)
    monkeypatch.setattr(main, "kb", KnowledgeBase(settings))
    body = TestClient(main.app).get("/api/health").json()
    assert body["ai"] is True and body["provider"] == "Gemini"
    assert body["model"] == settings.model and body["embedding_model"] is None
    assert body["knowledge"]["retrieval"] == "keyword"


def test_no_key_gives_a_clear_error_not_a_made_up_answer(client):
    r = client.post("/api/troubleshoot", json=BODY)
    assert r.status_code == 503 and r.json()["detail"]["code"] == "no_key"
    assert client.post("/api/chat", json={"question": "why?"}).status_code == 503


def test_troubleshoot(monkeypatch, keyed_client):
    monkeypatch.setattr(llm, "chat_json", Scripted(suggest()))
    r = keyed_client.post("/api/troubleshoot", json=BODY)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "suggest" and body["action"]["steps"] and body["sources"][0]["title"]
    assert keyed_client.get("/api/health").json()["ai"] is True


def test_prepare_fix_turn_and_artifact_are_returned(monkeypatch, keyed_client):
    reply = suggest()
    reply["action"].update(artifact_label="DAX measure", artifact="Total Sales = SUM(Sales[Amount])")
    monkeypatch.setattr(llm, "chat_json", Scripted(reply))
    r = keyed_client.post("/api/troubleshoot", json={
        **BODY,
        "turns": [{"type": "prepare_fix", "text": "Prepare a ready-to-apply fix"}],
    })
    assert r.status_code == 200
    assert r.json()["action"]["artifact_label"] == "DAX measure"
    assert r.json()["action"]["artifact"] == "Total Sales = SUM(Sales[Amount])"


def test_invalid_requests_are_rejected(client):
    assert client.post("/api/troubleshoot", json={"issue": "nope"}).status_code == 422
    assert client.post("/api/troubleshoot", json={**BODY, "error": "x" * 501}).status_code == 422
    assert client.post("/api/chat", json={"question": ""}).status_code == 422


def test_openai_error_becomes_a_friendly_message(monkeypatch, keyed_client):
    def boom(*a, **k):
        raise llm.AIUnavailable("auth", "OpenAI rejected the API key.")
    monkeypatch.setattr(llm, "chat_json", boom)
    r = keyed_client.post("/api/troubleshoot", json=BODY)
    assert r.status_code == 503 and r.json()["detail"] == {"code": "auth", "message": "OpenAI rejected the API key."}


def test_chat(monkeypatch, keyed_client):
    monkeypatch.setattr(llm, "chat_text", lambda s, system, user: "Check the gateway first.")
    r = keyed_client.post("/api/chat", json={"question": "Why would a refresh time out?"}).json()
    assert r["answer"] == "Check the gateway first." and r["basis"] == "knowledge_base" and r["sources"]


def test_resolved_cases_are_learned_only_after_approval(client):
    turns = [{"type": "suggestion", "title": "Reduce the data size", "steps": ["Remove columns"]},
             {"type": "feedback", "outcome": "still_failing"},
             {"type": "suggestion", "title": "Split the zebra dataset by quarter", "steps": ["Create two datasets"]}]
    case = client.post("/api/cases", json={"issue": "refresh_failed", "error": "Zebra export exceeded limit",
                                           "reports": ["NZ"], "turns": turns, "resolution": "Splitting fixed it"}).json()
    assert case["status"] == "pending" and case["tried"] == ["Reduce the data size"]
    assert case["worked"]["title"] == "Split the zebra dataset by quarter"

    kb = main.kb
    assert not any(h["kind"] == "case" for h in kb.search("Zebra export exceeded limit"))      # pending: invisible

    assert client.post(f"/api/cases/{case['id']}/approve").json()["status"] == "approved"
    top = kb.search("Zebra export exceeded limit")[0]
    assert top["kind"] == "case" and "zebra" in top["text"].lower()                            # approved: learned
    assert kb.info()["cases"] == 1

    assert client.post(f"/api/cases/{case['id']}/reject").json()["status"] == "rejected"
    assert kb.info()["cases"] == 0
    assert client.post("/api/cases/nope/approve").status_code == 404
    assert [c["id"] for c in client.get("/api/cases?status=rejected").json()] == [case["id"]]


def test_reindex(client):
    assert client.post("/api/reindex").json()["documents"] >= 15

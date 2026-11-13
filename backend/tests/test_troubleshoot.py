from dataclasses import replace

import pytest

from app import llm, troubleshoot
from app.schemas import TroubleshootRequest
from conftest import Scripted, escalate, suggest


def req(error="Timeout error", issue="refresh_failed", turns=None, **kw):
    return TroubleshootRequest(issue=issue, error=error, reports=["NZ_Accrual detail Report"], turns=turns or [], **kw)


def test_first_round_uses_guidance_and_excerpts(monkeypatch, keyed, kb_emb):
    ai = Scripted(suggest())
    monkeypatch.setattr(llm, "chat_json", ai)
    out = troubleshoot.run(keyed, kb_emb, req())
    system, user = ai.calls[0]
    assert "reduce the data size" in system.lower()                  # always-on company guidance
    assert "[S1]" in user and "Timeout error" in user                # retrieved excerpts and the error
    assert out["status"] == "suggest" and out["round"] == 1 and out["sources"]
    assert out["action"]["title"] == "Reduce the data size"


def test_prepare_fix_request_returns_a_copyable_artifact(monkeypatch, keyed, kb_emb):
    reply = suggest()
    reply["action"].update(artifact_label="Power Query M", artifact="let\n    Source = ...\nin\n    Source")
    ai = Scripted(reply)
    monkeypatch.setattr(llm, "chat_json", ai)
    turns = [{"type": "prepare_fix", "text": "Prepare the exact implementation"}]

    out = troubleshoot.run(keyed, kb_emb, req(turns=turns))

    assert "ready-to-apply implementation artifact" in ai.calls[0][1]
    assert out["action"]["artifact_label"] == "Power Query M"
    assert out["action"]["artifact"].startswith("let\n")


def test_feedback_is_sent_back_to_the_model(monkeypatch, keyed, kb_emb):
    ai = Scripted(suggest("Turn on incremental refresh"))
    monkeypatch.setattr(llm, "chat_json", ai)
    turns = [{"type": "suggestion", "title": "Reduce the data size", "steps": ["Remove columns"]},
             {"type": "feedback", "outcome": "still_failing", "note": "fails after 2 hours"}]
    out = troubleshoot.run(keyed, kb_emb, req(turns=turns))
    user = ai.calls[0][1]
    assert "Reduce the data size" in user and "problem is still there" in user and "fails after 2 hours" in user
    assert out["round"] == 2


def test_a_repeated_action_is_retried(monkeypatch, keyed, kb_emb):
    ai = Scripted(suggest("Reduce the data size"), suggest("Turn on incremental refresh"))
    monkeypatch.setattr(llm, "chat_json", ai)
    turns = [{"type": "suggestion", "title": "Reduce the data size", "steps": ["x"]},
             {"type": "feedback", "outcome": "still_failing"}]
    out = troubleshoot.run(keyed, kb_emb, req(turns=turns))
    assert out["action"]["title"] == "Turn on incremental refresh"
    assert len(ai.calls) == 2 and "repeated" in ai.calls[1][1]


def test_rounds_exhausted_escalates(monkeypatch, keyed, kb_emb):
    settings = replace(keyed, max_rounds=1)
    ai = Scripted(suggest("Another idea"), escalate())
    monkeypatch.setattr(llm, "chat_json", ai)
    turns = [{"type": "suggestion", "title": "Reduce the data size", "steps": ["x"]}, {"type": "feedback", "outcome": "still_failing"}]
    out = troubleshoot.run(settings, kb_emb, req(turns=turns))
    assert out["status"] == "escalate" and out["escalation"]["summary"] == "Please investigate."
    assert "No rounds are left" in ai.calls[0][1]


def test_escalation_is_built_if_the_model_will_not(monkeypatch, keyed, kb_emb):
    settings = replace(keyed, max_rounds=1)
    monkeypatch.setattr(llm, "chat_json", Scripted(suggest("Another idea")))
    turns = [{"type": "suggestion", "title": "Reduce the data size", "steps": ["x"]}]
    out = troubleshoot.run(settings, kb_emb, req(turns=turns))
    assert out["status"] == "escalate" and "Tried so far: Reduce the data size" in out["escalation"]["summary"]
    assert out["action"] is None


def test_knowledge_base_claim_is_downgraded_when_nothing_matched(monkeypatch, keyed, kb_lex):
    monkeypatch.setattr(llm, "chat_json", Scripted(suggest(used=("S1",))))
    out = troubleshoot.run(keyed, kb_lex, req(error="xqzv 0x8F2A91B3 qrz"))
    assert out["basis"] == "general_knowledge" and out["confidence"] != "high"


def test_invalid_answer_is_retried_then_accepted(monkeypatch, keyed, kb_emb):
    ai = Scripted({"status": "suggest"}, suggest())
    monkeypatch.setattr(llm, "chat_json", ai)
    assert troubleshoot.run(keyed, kb_emb, req())["status"] == "suggest"
    assert len(ai.calls) == 2


def test_two_invalid_answers_raise(monkeypatch, keyed, kb_emb):
    monkeypatch.setattr(llm, "chat_json", Scripted({"status": "ask"}))
    with pytest.raises(llm.AIUnavailable) as e:
        troubleshoot.run(keyed, kb_emb, req())
    assert e.value.code == "bad_answer"


def test_ask_round_returns_questions(monkeypatch, keyed, kb_emb):
    ask = {"status": "ask", "basis": "insufficient_information", "confidence": "low", "diagnosis": "Need more detail.",
           "causes": [], "action": None, "escalation": None, "used_sources": [],
           "questions": [{"text": "How long does it run?", "options": ["Minutes", "About 2 hours", "Other"]}]}
    monkeypatch.setattr(llm, "chat_json", Scripted(ask))
    out = troubleshoot.run(keyed, kb_emb, req())
    assert out["status"] == "ask" and out["questions"][0]["options"][1] == "About 2 hours" and out["action"] is None


def test_rls_requirement_reaches_the_model_with_rls_knowledge(monkeypatch, keyed, kb_emb):
    ai = Scripted(suggest("Create one role per country"))
    monkeypatch.setattr(llm, "chat_json", ai)
    r = TroubleshootRequest(issue="rls_missing", reports=["KR"], turns=[
        {"type": "message", "text": "Each country team sees only its own Country rows"}])
    troubleshoot.run(keyed, kb_emb, r)
    user = ai.calls[0][1]
    assert "Each country team sees only its own Country rows" in user and "Row-Level Security" in user
    assert "RLS" in user and "[S1]" in user


def test_answers_in_mixed_case_are_accepted(monkeypatch, keyed, kb_emb):
    loose = suggest()
    loose.update(status="Suggest", confidence="High", basis="Knowledge Base", causes=["Dataset too large"])
    monkeypatch.setattr(llm, "chat_json", Scripted(loose))
    out = troubleshoot.run(keyed, kb_emb, req())
    assert out["status"] == "suggest" and out["basis"] == "knowledge_base" and out["causes"][0]["cause"] == "Dataset too large"

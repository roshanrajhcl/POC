"""The interactive troubleshooting loop: retrieve, ask the AI, check the answer, return it.

The page sends the whole conversation each round, so the backend keeps no session.
Guardrails applied to every answer: valid shape, no repeated action, escalate when rounds are used up,
and never claim "from the knowledge base" when nothing relevant was found.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ValidationError
from typing_extensions import Literal

from . import llm, prompts
from .config import Settings
from .rag.kb import KnowledgeBase
from .rag.text import clean_error, tokens
from .schemas import Action, Cause, Escalation, Question, TroubleshootRequest

LEVEL = ("high", "medium", "low")


class LLMTurn(BaseModel):
    status: Literal["suggest", "ask", "escalate"]
    basis: Literal["knowledge_base", "general_knowledge", "insufficient_information"] = "general_knowledge"
    confidence: Literal["high", "medium", "low"] = "medium"
    diagnosis: str = ""
    causes: List[Cause] = Field(default_factory=list)
    action: Optional[Action] = None
    questions: List[Question] = Field(default_factory=list)
    escalation: Optional[Escalation] = None
    used_sources: List[str] = Field(default_factory=list)


def _norm(v: Any) -> Any:
    return str(v).strip().lower().replace(" ", "_") if isinstance(v, str) else v


def _validate(raw: Dict[str, Any]) -> LLMTurn:
    raw = dict(raw)
    for key in ("status", "basis", "confidence"):
        if key in raw:
            raw[key] = _norm(raw[key])
    raw["causes"] = [{"cause": c, "likelihood": "medium"} if isinstance(c, str) else {**c, "likelihood": _norm(c.get("likelihood", "medium"))}
                     for c in (raw.get("causes") or []) if c]
    if not raw.get("action"):
        raw["action"] = None
    if not raw.get("escalation"):
        raw["escalation"] = None
    try:
        t = LLMTurn.model_validate(raw)
    except ValidationError as e:
        raise ValueError(str(e.errors()[0].get("loc")) + " is invalid") from None
    if t.status == "suggest" and not (t.action and t.action.steps):
        raise ValueError("status is suggest but there is no action with steps")
    if t.status == "ask" and not t.questions:
        raise ValueError("status is ask but there are no questions")
    if t.status == "escalate" and not t.escalation:
        raise ValueError("status is escalate but there is no escalation")
    t.causes, t.questions = t.causes[:5], t.questions[:3]
    for q in t.questions:
        q.options = q.options[:5]
    if t.action:
        t.action.steps = t.action.steps[:8]
    return t


def _query(req: TroubleshootRequest) -> str:
    error = clean_error(req.error or "")
    # The issue label only helps when there is no error text; otherwise it would make an unfamiliar error
    # look related to every refresh document.
    parts = [error] if error else [prompts.ISSUE_LABEL.get(req.issue, "")]
    for t in req.turns[-6:]:
        if t.type == "message" and t.text:
            parts.append(t.text)
        elif t.type == "feedback" and t.note:
            parts.append(t.note)
        elif t.type == "answers":
            parts += [f"{i.question} {i.answer}" for i in t.items]
    return " ".join(p for p in parts if p)[:1500]


def _repeats(action: Optional[Action], tried: List[str]) -> bool:
    if not action:
        return False
    new = set(tokens(action.title))
    for old in tried:
        o = set(tokens(old))
        if new and o and len(new & o) / len(new | o) >= 0.75:
            return True
    return False


def _fallback_escalation(req: TroubleshootRequest, tried: List[str], diagnosis: str) -> Escalation:
    lines = [f"Problem: {req.error or req.issue} on {', '.join(req.reports[:10]) or 'the reports in the validation file'}.",
             "Tried so far: " + ("; ".join(tried) if tried else "nothing yet") + ".",
             f"Current understanding: {diagnosis or 'the cause is not yet known'}"]
    return Escalation(summary="\n".join(lines),
                      collect=["Full error text, error code and Activity ID from Refresh history",
                               "Start time, end time and duration of the failed run, and the last success",
                               "Capacity type, gateway name, and what changed recently"])


def _sources(t: LLMTurn, hits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    cited = []
    for s in t.used_sources:
        m = re.search(r"(\d+)", str(s))
        if m and 1 <= int(m.group(1)) <= len(hits):
            cited.append(hits[int(m.group(1)) - 1])
    pool = cited or [h for h in hits if h["relevant"]][:3]
    seen, out = set(), []
    for h in pool:
        if h["doc_id"] not in seen:
            seen.add(h["doc_id"])
            out.append({"id": h["id"], "title": h["title"], "section": h["section"], "kind": h["kind"], "relevance": h["relevance"]})
    return out


def run(settings: Settings, kb: KnowledgeBase, req: TroubleshootRequest) -> Dict[str, Any]:
    tried = [t.title for t in req.turns if t.type == "suggestion" and t.title]
    rounds = len(tried)
    exhausted = rounds >= settings.max_rounds
    hits = kb.search(_query(req))
    system = prompts.system_prompt(kb.always_text)

    extra, last_valid = "", None
    for _ in range(2):
        raw = llm.chat_json(settings, system, prompts.build_user(req, hits, rounds, settings.max_rounds, exhausted, extra))
        try:
            turn = _validate(raw)
        except ValueError as e:
            extra = f"\n\nYour previous reply was not valid: {e}. Reply again, as JSON in the required shape."
            continue
        last_valid = turn
        if exhausted and turn.status != "escalate":
            extra = "\n\nNo rounds are left. Set status to escalate and write the escalation summary."
            continue
        if _repeats(turn.action, tried):
            extra = f"\n\nYour previous reply repeated an action that was already tried (\"{turn.action.title}\"). Give a different action."
            continue
        break
    if last_valid is None:
        raise llm.AIUnavailable("bad_answer", "The AI provider returned an answer in an unexpected format. Try again.")

    turn = last_valid
    if exhausted and turn.status != "escalate":      # the model would not escalate: build the hand-off ourselves
        turn.status, turn.action, turn.questions = "escalate", None, []
        turn.escalation = _fallback_escalation(req, tried, turn.diagnosis)

    sources = _sources(turn, hits)
    relevant = any(h["relevant"] for h in hits)
    if turn.basis == "knowledge_base" and not (relevant and sources):
        turn.basis = "general_knowledge"
    if not relevant and turn.confidence == "high":
        turn.confidence = "medium"

    return {"status": turn.status, "basis": turn.basis, "confidence": turn.confidence, "diagnosis": turn.diagnosis,
            "causes": [c.model_dump() for c in turn.causes], "action": turn.action.model_dump() if turn.action else None,
            "questions": [q.model_dump() for q in turn.questions],
            "escalation": turn.escalation.model_dump() if turn.escalation else None,
            "sources": sources, "round": rounds + 1}

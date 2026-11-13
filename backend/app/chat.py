"""Free-text questions from the side panel, answered from the knowledge base by the AI."""
from __future__ import annotations

from typing import Any, Dict, Optional

from . import llm, prompts
from .config import Settings
from .rag.kb import KnowledgeBase


def answer(settings: Settings, kb: KnowledgeBase, question: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    hits = kb.search(question)
    text = llm.chat_text(settings, prompts.chat_system(kb.always_text), prompts.chat_user(question, context, hits))
    relevant = [h for h in hits if h["relevant"]]
    seen, sources = set(), []
    for h in relevant[:4]:
        if h["doc_id"] not in seen:
            seen.add(h["doc_id"])
            sources.append({"id": h["id"], "title": h["title"], "section": h["section"], "kind": h["kind"], "relevance": h["relevance"]})
    return {"answer": text, "sources": sources, "basis": "knowledge_base" if relevant else "general_knowledge"}

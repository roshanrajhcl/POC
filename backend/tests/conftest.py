import hashlib
import math

import pytest

from app.config import Settings
from app.rag.kb import KnowledgeBase
from app.rag.text import tokens


def fake_embed(texts):
    """Deterministic stand-in for OpenAI embeddings: a hashed bag of words."""
    out = []
    for t in texts:
        v = [0.0] * 64
        for tok in tokens(t):
            v[int(hashlib.md5(tok.encode()).hexdigest(), 16) % 64] += 1.0
        n = math.sqrt(sum(x * x for x in v)) or 1.0
        out.append([x / n for x in v])
    return out


@pytest.fixture
def keyless(tmp_path):
    return Settings(data_dir=tmp_path)


@pytest.fixture
def keyed(tmp_path):
    return Settings(openai_api_key="sk-test", data_dir=tmp_path)


@pytest.fixture
def kb_lex(keyless):
    return KnowledgeBase(keyless)


@pytest.fixture
def kb_emb(keyed):
    return KnowledgeBase(keyed, embed_fn=fake_embed)


class Scripted:
    """Replaces llm.chat_json: returns the scripted replies in order (the last one repeats) and records the prompts."""

    def __init__(self, *replies):
        self.replies, self.calls = list(replies), []

    def __call__(self, settings, system, user):
        self.calls.append((system, user))
        return self.replies.pop(0) if len(self.replies) > 1 else self.replies[0]


def suggest(title="Reduce the data size", basis="knowledge_base", confidence="high", used=("S1",)):
    return {"status": "suggest", "basis": basis, "confidence": confidence, "diagnosis": "Likely a large dataset.",
            "causes": [{"cause": "Dataset too large", "likelihood": "high"}],
            "action": {"title": title, "steps": ["Step one", "Step two"], "verify": "Refresh finishes"},
            "questions": [], "escalation": None, "used_sources": list(used)}


def escalate():
    return {"status": "escalate", "basis": "general_knowledge", "confidence": "low", "diagnosis": "Not resolved.",
            "causes": [], "action": None, "questions": [],
            "escalation": {"summary": "Please investigate.", "collect": ["Activity ID"]}, "used_sources": []}

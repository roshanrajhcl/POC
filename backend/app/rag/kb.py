"""The knowledge base: documents and approved cases, searched by meaning (embeddings) and by keyword together.

If embeddings are unavailable (no key, or the model is not allowed) search quietly continues with keywords only.
"""
from __future__ import annotations

import logging
import threading
from typing import Any, Callable, Dict, List, Optional

from .. import llm
from ..cases import CaseStore
from ..config import Settings
from .index import BM25, EmbeddingCache, cosine, fuse, rank
from .loader import Chunk, load_documents
from .text import clean_error, tokens

log = logging.getLogger("reportpulse.rag")
MAX_PER_DOC = 3


class KnowledgeBase:
    def __init__(self, settings: Settings, embed_fn: Optional[Callable[[List[str]], List[List[float]]]] = None):
        self.s = settings
        self._embed = embed_fn or (lambda texts: llm.embed(settings, texts))
        self.cases = CaseStore(settings.data_dir / "cases.json")
        self._lock = threading.RLock()
        self.reload()

    # ---- loading -------------------------------------------------------------------------------------------
    def reload(self) -> None:
        with self._lock:
            chunks, self._always, self._docs = load_documents(self.s.knowledge_dir)
            cases = self.cases.approved_chunks()
            self._chunks: List[Chunk] = chunks + cases
            self._n_cases = len(cases)
            self._bm25 = BM25([tokens(c.index_text) for c in self._chunks])
            self._vectors: Dict[str, List[float]] = {}
            self._state = "pending" if self.s.embeddings_enabled else "off"   # off | pending | ready | failed

    @property
    def always_text(self) -> str:
        return self._always

    def info(self) -> Dict[str, Any]:
        retrieval = {"ready": "embeddings", "pending": "embeddings (not built yet)"}.get(self._state, "keyword")
        return {"documents": self._docs, "chunks": len(self._chunks), "cases": self._n_cases, "retrieval": retrieval}

    def warm(self) -> None:
        self._ensure_vectors()

    def _ensure_vectors(self) -> None:
        with self._lock:
            if self._state != "pending":
                return
            try:
                cache = EmbeddingCache(self.s.data_dir / "embeddings.json", self.s.embedding_model)
                missing = [c for c in self._chunks if cache.get(c.index_text) is None]
                for i in range(0, len(missing), 64):
                    batch = missing[i:i + 64]
                    for c, v in zip(batch, self._embed([c.index_text for c in batch])):
                        cache.put(c.index_text, v)
                if missing:
                    cache.save()
                self._vectors = {c.id: cache.get(c.index_text) for c in self._chunks}
                self._state = "ready"
                log.info("Embeddings ready for %d chunks", len(self._chunks))
            except Exception as e:  # noqa: BLE001
                log.warning("Embeddings unavailable (%s); using keyword search", getattr(e, "code", type(e).__name__))
                self._state = "failed"

    # ---- search --------------------------------------------------------------------------------------------
    def _relevance(self, cos: Optional[float], cov: float) -> str:
        level = "low"
        if cos is not None:
            level = "high" if cos >= 0.45 else "medium" if cos >= self.s.min_cosine else "low"
        if cov >= 0.6:
            level = "high"
        elif cov >= self.s.min_coverage and level == "low":
            level = "medium"
        return level

    def search(self, query: str, k: Optional[int] = None) -> List[Dict[str, Any]]:
        k = k or self.s.top_k
        self._ensure_vectors()
        q = clean_error(query)
        with self._lock:
            chunks, bm25, vectors, state = self._chunks, self._bm25, self._vectors, self._state
        if not chunks:
            return []
        bm, cov = bm25.scores(tokens(q))
        rankings = [rank(bm)]
        cos: Optional[List[float]] = None
        if state == "ready" and q:
            try:
                qv = self._embed([q])[0]
                cos = [cosine(qv, vectors[c.id]) for c in chunks]
                rankings.append(rank(cos))
            except Exception as e:  # noqa: BLE001
                log.warning("Query embedding failed (%s); keyword only for this search", getattr(e, "code", type(e).__name__))
        fused = fuse(rankings)
        hits: List[Dict[str, Any]] = []
        per_doc: Dict[str, int] = {}
        for i in sorted(fused, key=lambda j: -fused[j]):
            c = chunks[i]
            if per_doc.get(c.doc_id, 0) >= MAX_PER_DOC:
                continue
            per_doc[c.doc_id] = per_doc.get(c.doc_id, 0) + 1
            rel = self._relevance(cos[i] if cos is not None else None, cov[i])
            hits.append({"id": c.id, "doc_id": c.doc_id, "title": c.title, "section": c.section, "kind": c.kind,
                         "text": c.text, "relevance": rel, "relevant": rel != "low"})
            if len(hits) >= k:
                break
        return hits

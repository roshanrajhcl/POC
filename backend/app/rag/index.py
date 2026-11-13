"""Search math: BM25 keyword scoring, cosine similarity, and the on-disk embedding cache."""
from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class BM25:
    def __init__(self, docs: List[List[str]], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.tf = [Counter(d) for d in docs]
        self.len = [len(d) for d in docs]
        self.n = len(docs)
        self.avg = (sum(self.len) / self.n) if self.n else 0.0
        df: Counter = Counter()
        for c in self.tf:
            df.update(c.keys())
        self.idf = {t: math.log(1 + (self.n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def scores(self, query: List[str]) -> Tuple[List[float], List[float]]:
        """Returns (bm25 score, coverage) for every document.

        Coverage is the share of the query's informative terms (weighted by rarity) found in the document,
        a 0..1 value that does not depend on query length.
        """
        # Query words the knowledge base has never seen count as the rarest (most informative) words,
        # so a query full of unfamiliar words cannot look like a strong match to a few common ones.
        top = max(self.idf.values()) if self.idf else 1.0
        all_terms = set(query)
        terms = [t for t in all_terms if t in self.idf]
        total = sum(self.idf.get(t, top) for t in all_terms) or 1.0
        scores, coverage = [], []
        for i in range(self.n):
            s = hit = 0.0
            for t in terms:
                f = self.tf[i].get(t, 0)
                if f:
                    s += self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * self.len[i] / (self.avg or 1)))
                    hit += self.idf[t]
            scores.append(s)
            coverage.append(hit / total if all_terms else 0.0)
        return scores, coverage


def cosine(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def rank(values: List[float]) -> List[int]:
    """Document indexes ordered best first, ignoring zero scores."""
    return [i for i, v in sorted(enumerate(values), key=lambda p: -p[1]) if v > 0]


def fuse(rankings: List[List[int]], k: int = 60) -> Dict[int, float]:
    """Reciprocal rank fusion: combine several rankings into one score per document."""
    out: Dict[int, float] = {}
    for r in rankings:
        for pos, i in enumerate(r):
            out[i] = out.get(i, 0.0) + 1.0 / (k + pos + 1)
    return out


class EmbeddingCache:
    """Vectors saved on disk, keyed by a hash of the model and text, so unchanged text is never embedded twice."""

    def __init__(self, path: Path, model: str):
        self.path, self.model = Path(path), model
        self.items: Dict[str, List[float]] = {}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if data.get("model") == model:
                self.items = data.get("items", {})
        except (OSError, ValueError):
            pass

    def key(self, text: str) -> str:
        return hashlib.sha256(f"{self.model}\n{text}".encode("utf-8")).hexdigest()

    def get(self, text: str) -> Optional[List[float]]:
        return self.items.get(self.key(text))

    def put(self, text: str, vec: List[float]) -> None:
        self.items[self.key(text)] = vec

    def save(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps({"model": self.model, "items": self.items}), encoding="utf-8")
        except OSError:
            pass  # the cache is an optimisation only

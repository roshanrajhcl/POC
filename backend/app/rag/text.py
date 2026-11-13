"""Text helpers shared by the keyword search and the query builder."""
from __future__ import annotations

import re
from typing import List

_STOP = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have", "in", "is", "it", "its",
    "of", "on", "or", "that", "the", "this", "to", "was", "were", "will", "with", "any", "not", "no", "can",
    "do", "does", "did", "how", "i", "we", "you", "my", "our", "your", "what", "when", "which", "who", "why",
    "then", "than", "so", "if", "but", "into", "out", "up", "all", "also", "should", "would", "could",
}

_GUID = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")
_DATE = re.compile(r"\b\d{1,4}[/-]\d{1,2}[/-]\d{1,4}\b")
_TIME = re.compile(r"\b\d{1,2}:\d{2}(:\d{2})?\s?(AM|PM)?\b", re.I)
_LONGNUM = re.compile(r"\b\d{6,}\b")


def clean_error(text: str) -> str:
    """Strip ids, dates and long numbers so the same error from different runs looks the same."""
    text = _GUID.sub(" ", text or "")
    text = _DATE.sub(" ", text)
    text = _TIME.sub(" ", text)
    text = _LONGNUM.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def _stem(t: str) -> str:
    if len(t) > 6 and t.endswith("ing"):
        return t[:-3]
    if len(t) > 5 and t.endswith("ed"):
        return t[:-2]
    if len(t) > 4 and t.endswith("s") and not t.endswith("ss"):
        return t[:-1]
    return t


def tokens(text: str) -> List[str]:
    return [_stem(t) for t in re.findall(r"[a-z0-9]+", (text or "").lower()) if len(t) > 1 and t not in _STOP]

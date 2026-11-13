"""Loads knowledge documents (Markdown with a small header) and splits them into chunks.

Header fields: id, title, category, keywords, source, always.
A document with `always: true` is not searched; its text is given to the AI on every request.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple


@dataclass
class Chunk:
    id: str
    doc_id: str
    title: str
    section: str
    text: str          # shown to the model
    index_text: str    # searched (adds the keywords)
    kind: str = "document"   # document | case
    source: str = ""


def parse_document(raw: str) -> Tuple[Dict[str, str], str]:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", raw, re.S)
    if not m:
        raise ValueError("missing header")
    meta: Dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip().lower()] = v.strip().strip('"')
    if "id" not in meta or "title" not in meta:
        raise ValueError("header needs id and title")
    return meta, m.group(2).strip()


def _sections(body: str) -> List[Tuple[str, str]]:
    parts = re.split(r"^## +(.+)$", body, flags=re.M)
    out: List[Tuple[str, str]] = []
    if parts[0].strip():
        out.append(("Overview", parts[0].strip()))
    for i in range(1, len(parts), 2):
        text = parts[i + 1].strip()
        if text:
            out.append((parts[i].strip(), text))
    return out


def load_documents(folder: Path) -> Tuple[List[Chunk], str, int]:
    """Returns (chunks, always_text, number_of_documents)."""
    chunks: List[Chunk] = []
    always: List[str] = []
    docs = 0
    for path in sorted(Path(folder).glob("*.md")):
        meta, body = parse_document(path.read_text(encoding="utf-8"))
        docs += 1
        if meta.get("always", "").lower() == "true":
            always.append(body)
            continue
        keywords = meta.get("keywords", "")
        for n, (section, text) in enumerate(_sections(body), 1):
            chunks.append(Chunk(
                id=f"{meta['id']}#{n}", doc_id=meta["id"], title=meta["title"], section=section,
                text=text, index_text=f"{meta['title']}. {section}. {keywords}. {text}",
                source=meta.get("source", ""),
            ))
    return chunks, "\n\n".join(always), docs

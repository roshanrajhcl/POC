"""Resolved cases: what worked for a real error. Saved as pending, searchable only after a person approves them."""
from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .rag.loader import Chunk


def build_case(issue: str, error: Optional[str], reports: List[str], turns: List[Any], resolution: Optional[str]) -> Dict[str, Any]:
    """Derives what was tried and what worked from the conversation turns."""
    suggestions = [t for t in turns if t.type == "suggestion" and t.title]
    worked = suggestions[-1] if suggestions else None
    return {
        "issue": issue,
        "error": error,
        "reports": reports[:20],
        "tried": [t.title for t in suggestions[:-1]],
        "worked": {"title": worked.title, "steps": list(worked.steps)} if worked else None,
        "resolution": (resolution or "").strip() or None,
    }


def case_text(case: Dict[str, Any]) -> str:
    parts = [f"Resolved case for {case.get('issue')}."]
    if case.get("error"):
        parts.append(f"Error: {case['error']}.")
    if case.get("tried"):
        parts.append("Tried first and did not fix it: " + "; ".join(case["tried"]) + ".")
    worked = case.get("worked")
    if worked:
        parts.append(f"What fixed it: {worked['title']}. Steps: " + " ".join(worked.get("steps", [])))
    if case.get("resolution"):
        parts.append(f"Note from the person who fixed it: {case['resolution']}")
    return " ".join(parts)


class CaseStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self._lock = threading.Lock()

    def _read(self) -> List[Dict[str, Any]]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return []

    def _write(self, items: List[Dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(items, indent=2), encoding="utf-8")

    def add(self, data: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            items = self._read()
            case = {"id": uuid.uuid4().hex[:10], "status": "pending",
                    "created": datetime.now(timezone.utc).isoformat(timespec="seconds"), **data}
            items.append(case)
            self._write(items)
            return case

    def list(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        items = self._read()
        return [c for c in items if status in (None, c.get("status"))]

    def set_status(self, case_id: str, status: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            items = self._read()
            for c in items:
                if c["id"] == case_id:
                    c["status"] = status
                    self._write(items)
                    return c
        return None

    def approved_chunks(self) -> List[Chunk]:
        out = []
        for c in self.list("approved"):
            text = case_text(c)
            title = f"Resolved case: {c.get('error') or c.get('issue')}"
            out.append(Chunk(id=f"case-{c['id']}#1", doc_id=f"case-{c['id']}", title=title, section="What worked",
                             text=text, index_text=f"{title}. {text}", kind="case", source="Approved resolved case"))
        return out

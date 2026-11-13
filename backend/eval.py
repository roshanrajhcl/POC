"""Runs scripted scenarios against the REAL AI and prints PASS or FAIL for each. Needs the key. From the project root:

    backend\\.venv\\Scripts\\python backend\\eval.py

Shows whether the assistant follows the company guidance, adapts when a fix fails, copes with a new error,
and asks about RLS. Answers can vary a little between runs, so a single FAIL is a prompt to look, not a verdict.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app import llm, troubleshoot  # noqa: E402
from app.config import load_settings  # noqa: E402
from app.rag.kb import KnowledgeBase  # noqa: E402
from app.schemas import TroubleshootRequest  # noqa: E402

s = load_settings()
kb = KnowledgeBase(s)
results = []


def text_of(out):
    parts = [out["diagnosis"]]
    if out["action"]:
        parts += [out["action"]["title"], *out["action"]["steps"], out["action"]["verify"]]
    parts += [q["text"] for q in out["questions"]]
    if out["escalation"]:
        parts.append(out["escalation"]["summary"])
    return " ".join(parts).lower()


def case(name, check, **req):
    try:
        out = troubleshoot.run(s, kb, TroubleshootRequest(**req))
        ok, note = check(out, text_of(out))
    except llm.AIUnavailable as e:
        ok, note = False, f"AI unavailable [{e.code}] {e.message}"
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f"\n      {note}"))


# 1. The two fixes from the brief come first
case("Timeout: first suggestion is to reduce the data size",
     lambda o, t: (o["status"] == "suggest" and "data size" in t or ("reduce" in t and "column" in t), t[:200]),
     issue="refresh_failed", error="Timeout error", reports=["NZ"])
case("Processing error: first suggestion is gateway and credentials",
     lambda o, t: ("gateway" in t and "credential" in t, t[:200]),
     issue="refresh_failed", error="An error occurred while processing", reports=["CN"])

# 2. It adapts when the first fix did not work
tried = [{"type": "suggestion", "title": "Reduce the data size", "steps": ["Remove unused columns", "Filter old rows"]},
         {"type": "feedback", "outcome": "still_failing", "note": "Removed columns and filtered to 2 years, still times out"}]
case("Timeout: after 'still failing' it does not repeat reducing the data size",
     lambda o, t: (o["status"] in ("suggest", "ask") and "reduce the data size" not in (o["action"] or {}).get("title", "").lower(), t[:200]),
     issue="refresh_failed", error="Timeout error", reports=["NZ"], turns=tried)
case("Timeout: with 'fails after 2 hours on Pro' it points to the time limit or incremental refresh",
     lambda o, t: (("2 hour" in t or "limit" in t or "incremental" in t), t[:200]),
     issue="refresh_failed", error="Timeout error", reports=["NZ"],
     turns=tried + [{"type": "answers", "items": [{"question": "How long does it run before failing?", "answer": "About 2 hours"},
                                                    {"question": "Which license?", "answer": "Pro"}]}])
case("Rounds used up: it escalates with a summary",
     lambda o, t: (o["status"] == "escalate" and bool(o["escalation"]["summary"]), t[:200]),
     issue="refresh_failed", error="Timeout error", reports=["NZ"],
     turns=[{"type": "suggestion", "title": f"Attempt {i}", "steps": ["x"]} for i in range(s.max_rounds)])

# 3. New errors
case("New error (not in the knowledge base wording): points at a renamed or missing table, sheet or column",
     lambda o, t: (any(w in t for w in ("renamed", "column", "sheet", "table", "step")) and o["basis"] != "insufficient_information", t[:200]),
     issue="refresh_failed", error="DataSource.Error: The key didn't match any rows in the table", reports=["JP"])
case("Truly unknown error: not claimed as certain",
     lambda o, t: (o["confidence"] != "high" and o["basis"] != "knowledge_base", f"basis={o['basis']} confidence={o['confidence']}"),
     issue="refresh_failed", error="Error code 0x8F2A91B3 in module QRZ", reports=["JP"])

# 4. Row-Level Security
case("RLS with a requirement: gives role names, a DAX filter and a View as test",
     lambda o, t: ("[country]" in t and "view as" in t, t[:200]),
     issue="rls_missing", reports=["KR", "AU"],
     turns=[{"type": "message", "text": "Each country team only sees its own country. The table has a Country column (KR, AU, NZ). Users are in groups like KR-Finance."}])
case("RLS without a requirement: asks how access should work",
     lambda o, t: (o["status"] == "ask" or "?" in t, t[:200]),
     issue="rls_missing", reports=["KR", "AU"])

# 5. Search itself
top = kb.search("Timeout error")[0]["doc_id"]
ok = top == "refresh-timeout"
results.append(ok)
print(f"{'PASS' if ok else 'FAIL'}  Search: 'Timeout error' finds the timeout document (top hit: {top}, search: {kb.info()['retrieval']})")

print(f"\n{sum(results)} of {len(results)} passed")
sys.exit(0 if all(results) else 1)

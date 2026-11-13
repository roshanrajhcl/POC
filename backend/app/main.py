import logging
import threading
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException

from . import chat, llm, troubleshoot
from .cases import build_case
from .config import load_settings
from .rag.kb import KnowledgeBase
from .schemas import (CaseIn, CaseOut, ChatRequest, ChatResponse, Health, TroubleshootRequest, TroubleshootResponse)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("reportpulse")

settings = load_settings()
kb = KnowledgeBase(settings)


@asynccontextmanager
async def lifespan(_app):
    log.info("Started: %r, knowledge=%s", settings, kb.info())       # repr hides the key
    if settings.embeddings_enabled:
        threading.Thread(target=kb.warm, daemon=True).start()          # build embeddings in the background
    yield


app = FastAPI(title="ReportPulse backend", docs_url="/api/docs", openapi_url="/api/openapi.json", lifespan=lifespan)


def _unavailable(e: llm.AIUnavailable) -> HTTPException:
    return HTTPException(e.status, detail={"code": e.code, "message": e.message})


@app.get("/api/health", response_model=Health)
def health():
    return Health(status="ok", ai=settings.ai_enabled, provider=settings.provider_name,
                  model=settings.model if settings.ai_enabled else None,
                  embedding_model=settings.embedding_model if settings.embeddings_enabled else None,
                  knowledge=kb.info())


@app.post("/api/troubleshoot", response_model=TroubleshootResponse)
def troubleshoot_endpoint(req: TroubleshootRequest):
    try:
        return troubleshoot.run(settings, kb, req)
    except llm.AIUnavailable as e:
        raise _unavailable(e)


@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    try:
        return chat.answer(settings, kb, req.question, req.context)
    except llm.AIUnavailable as e:
        raise _unavailable(e)


# ---- resolved cases: saved as pending, searchable only after approval ------------------------------------------
@app.post("/api/cases", response_model=CaseOut)
def save_case(body: CaseIn):
    return kb.cases.add(build_case(body.issue, body.error, body.reports, body.turns, body.resolution))


@app.get("/api/cases", response_model=List[CaseOut])
def list_cases(status: Optional[str] = None):
    return kb.cases.list(status)


def _set_case(case_id: str, status: str):
    case = kb.cases.set_status(case_id, status)
    if case is None:
        raise HTTPException(404, detail={"code": "not_found", "message": "No such case."})
    kb.reload()
    return case


@app.post("/api/cases/{case_id}/approve", response_model=CaseOut)
def approve_case(case_id: str):
    return _set_case(case_id, "approved")


@app.post("/api/cases/{case_id}/reject", response_model=CaseOut)
def reject_case(case_id: str):
    return _set_case(case_id, "rejected")


@app.post("/api/reindex")
def reindex():
    """Reload the knowledge documents after editing files in backend/knowledge."""
    kb.reload()
    return kb.info()

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from typing_extensions import Literal

Issue = Literal["refresh_failed", "refresh_not_configured", "rls_missing", "refresh_stale", "general_analysis"]
Level = Literal["high", "medium", "low"]


# ---- troubleshooting conversation ------------------------------------------------------------------------------
class QA(BaseModel):
    question: str = Field(max_length=500)
    answer: str = Field(max_length=1000)


class Turn(BaseModel):
    """One step of the conversation, sent back by the page every round (the backend keeps no session)."""
    type: Literal["suggestion", "feedback", "answers", "message", "prepare_fix"]
    title: Optional[str] = Field(default=None, max_length=200)                  # suggestion
    steps: List[str] = Field(default_factory=list, max_length=12)               # suggestion
    artifact_label: Optional[str] = Field(default=None, max_length=100)         # suggestion
    artifact: Optional[str] = Field(default=None, max_length=12000)             # suggestion
    outcome: Optional[Literal["still_failing", "cant_do", "different_error", "info"]] = None   # feedback
    note: Optional[str] = Field(default=None, max_length=2000)                  # feedback
    items: List[QA] = Field(default_factory=list, max_length=6)                 # answers
    text: Optional[str] = Field(default=None, max_length=2000)                  # message


class TroubleshootRequest(BaseModel):
    issue: Issue
    file_type: Optional[str] = None
    error: Optional[str] = Field(default=None, max_length=500)
    reports: List[str] = Field(default_factory=list, max_length=200)
    rows: List[Dict[str, Any]] = Field(default_factory=list, max_length=50)
    turns: List[Turn] = Field(default_factory=list, max_length=40)
    context: Optional[Dict[str, Any]] = None


class Cause(BaseModel):
    cause: str
    likelihood: Level = "medium"


class Action(BaseModel):
    title: str
    steps: List[str]
    verify: str = ""
    artifact_label: Optional[str] = Field(default=None, max_length=100)
    artifact: Optional[str] = Field(default=None, max_length=12000)


class Question(BaseModel):
    text: str
    options: List[str] = Field(default_factory=list)


class Escalation(BaseModel):
    summary: str
    collect: List[str] = Field(default_factory=list)


class Source(BaseModel):
    id: str
    title: str
    section: str
    kind: str
    relevance: str


class TroubleshootResponse(BaseModel):
    status: Literal["suggest", "ask", "escalate"]
    basis: Literal["knowledge_base", "general_knowledge", "insufficient_information"]
    confidence: Level
    diagnosis: str
    causes: List[Cause]
    action: Optional[Action] = None
    questions: List[Question]
    escalation: Optional[Escalation] = None
    sources: List[Source]
    round: int


# ---- chat ------------------------------------------------------------------------------------------------------
class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    answer: str
    sources: List[Source]
    basis: Literal["knowledge_base", "general_knowledge"]


# ---- resolved cases --------------------------------------------------------------------------------------------
class CaseIn(BaseModel):
    issue: Issue
    error: Optional[str] = Field(default=None, max_length=500)
    reports: List[str] = Field(default_factory=list, max_length=200)
    turns: List[Turn] = Field(default_factory=list, max_length=40)
    resolution: Optional[str] = Field(default=None, max_length=1000)


class CaseOut(BaseModel):
    id: str
    status: str
    created: str
    issue: str
    error: Optional[str] = None
    tried: List[str] = Field(default_factory=list)
    worked: Optional[Dict[str, Any]] = None
    resolution: Optional[str] = None


class Health(BaseModel):
    status: Literal["ok"]
    ai: bool
    provider: str
    model: Optional[str]
    embedding_model: Optional[str]
    knowledge: Dict[str, Any]

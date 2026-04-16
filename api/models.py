# =============================================================
# api/models.py — Modèles Pydantic (requêtes & réponses)
# =============================================================

from pydantic import BaseModel
from typing import List, Optional


class QueryRequest(BaseModel):
    question: str
    show_sources: bool = True


class SourceDocument(BaseModel):
    source: str
    content: str


class QueryResponse(BaseModel):
    answer: str
    sources: Optional[List[SourceDocument]] = None


class StatusResponse(BaseModel):
    status: str
    documents_loaded: bool
    vector_store_exists: bool
    total_documents: int


class DocumentInfo(BaseModel):
    filename: str
    size: int
    type: str


class MessageResponse(BaseModel):
    message: str

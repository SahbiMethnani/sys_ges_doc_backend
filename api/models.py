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


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    display_name: str | None = None
    email: str | None = None


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    refresh_token: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str | None = None
    display_name: str | None = None
    role: str

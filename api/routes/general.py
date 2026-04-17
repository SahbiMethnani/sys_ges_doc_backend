# =============================================================
# api/routes/general.py — Endpoints généraux (/, /status)
# =============================================================

import os
from pathlib import Path
from fastapi import APIRouter

from api.models import StatusResponse
from api.dependencies import get_rag
from config import DOCUMENTS_FOLDER
from vectorstore import vector_index_exists

router = APIRouter(tags=["Général"])


@router.get("/")
async def root():
    """Page d'accueil de l'API."""
    return {
        "message": "API RAG — Système de Questions-Réponses",
        "docs": "/docs",
        "version": "1.0.0",
    }


@router.get("/status", response_model=StatusResponse)
async def get_status():
    """Statut du système RAG."""
    rag = get_rag()
    files = [f for f in Path(DOCUMENTS_FOLDER).rglob("*") if f.is_file()]

    return StatusResponse(
        status="online",
        documents_loaded=rag is not None and rag.vectorstore is not None,
        vector_store_exists=vector_index_exists(),
        total_documents=len(files),
    )

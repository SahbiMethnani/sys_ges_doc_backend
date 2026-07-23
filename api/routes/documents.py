# =============================================================
# api/routes/documents.py — Endpoints /documents
# =============================================================

import os
import sys
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

from api.auth.dependencies import require_admin
from api.db.models import User
from api.models import DocumentInfo, MessageResponse
from api.dependencies import get_rag, set_rag
from config import DOCUMENTS_FOLDER, LANCE_DB_PATH, SUPPORTED_EXTENSIONS

# ✅ Import au niveau module → patch("api.routes.documents.load_documents") fonctionne
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from loader import load_documents
from vectorstore import build_vectorstore

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("", response_model=list[DocumentInfo])
async def list_documents(_admin: User = Depends(require_admin)):
    """Liste tous les documents présents dans le dossier."""
    documents = []
    for file_path in Path(DOCUMENTS_FOLDER).rglob("*"):
        if file_path.is_file():
            documents.append(DocumentInfo(
                filename=file_path.name,
                size=file_path.stat().st_size,
                type=file_path.suffix,
            ))
    return documents


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    _admin: User = Depends(require_admin),
):
    """
    Uploade un nouveau document.
    Formats acceptés : .pdf, .html, .txt, .raw
    """
    ext = Path(file.filename).suffix.lower()

    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Format non supporté. Formats acceptés : {', '.join(SUPPORTED_EXTENSIONS)}",
        )

    try:
        file_path = Path(DOCUMENTS_FOLDER) / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return {
            "message": "Fichier uploadé avec succès",
            "filename": file.filename,
            "size": file_path.stat().st_size,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/index")
async def index_documents(_admin: User = Depends(require_admin)):
    """
    Réindexe tous les documents du dossier dans LanceDB.
    À appeler après chaque upload.
    """
    rag = get_rag()
    if rag is None:
        raise HTTPException(status_code=503, detail="Système RAG non initialisé.")

    try:
        if os.path.isdir(LANCE_DB_PATH):
            shutil.rmtree(LANCE_DB_PATH, ignore_errors=True)

        documents = load_documents(DOCUMENTS_FOLDER)
        if not documents:
            raise HTTPException(status_code=400, detail="Aucun document trouvé dans le dossier.")

        rag.vectorstore = build_vectorstore(documents, rag.embeddings)
        rag.reset_qa_chain()

        return {
            "message": "Indexation réussie",
            "documents_indexed": len(documents),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{filename}", response_model=MessageResponse)
async def delete_document(
    filename: str,
    _admin: User = Depends(require_admin),
):
    """Supprime un document du dossier."""
    file_path = Path(DOCUMENTS_FOLDER) / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Document non trouvé.")

    try:
        file_path.unlink()
        return MessageResponse(message=f"Document '{filename}' supprimé avec succès.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
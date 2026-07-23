# =============================================================
# tests/api/conftest.py — Fixtures pour les tests FastAPI
# =============================================================

import io
import os
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture()
def client(tmp_path):
    """
    Instancie l'application FastAPI avec tous les composants lourds mockés.
    DOCUMENTS_FOLDER est redirigé vers tmp_path pour les tests d'upload.
    """
    from langchain_core.documents import Document
    from fastapi.testclient import TestClient

    # Dossier temporaire pour les uploads
    docs_dir = str(tmp_path / "documents")
    os.makedirs(docs_dir, exist_ok=True)

    # Documents et résultat RAG factices
    fake_docs = [
        Document(page_content="Python est un langage de programmation.",
                 metadata={"source": "doc1.txt"}),
        Document(page_content="LanceDB est une base vectorielle.",
                 metadata={"source": "doc2.txt"}),
    ]
    fake_rag_result = {
        "result": "Python est un langage de programmation.",
        "source_documents": fake_docs,
    }

    # Mocks des composants lourds
    mock_embeddings = MagicMock()
    mock_embeddings.embed_query.return_value     = [0.1, 0.2, 0.3]
    mock_embeddings.embed_documents.return_value = [[0.1, 0.2, 0.3]]

    mock_llm = MagicMock()
    mock_llm.invoke.return_value = "Réponse simulée."

    mock_vs = MagicMock()
    retriever = MagicMock()
    retriever.invoke.return_value = fake_docs
    mock_vs.as_retriever.return_value = retriever

    mock_rag = MagicMock()
    mock_rag.query.return_value = fake_rag_result
    mock_rag.vectorstore = mock_vs
    mock_rag.embeddings = mock_embeddings

    with patch("config.AUTH_DISABLED", True), \
         patch("api.auth.dependencies.AUTH_DISABLED", True), \
         patch("api.main.get_embeddings",              return_value=mock_embeddings), \
         patch("api.main.get_llm",                     return_value=mock_llm), \
         patch("api.main.vector_index_exists",         return_value=True), \
         patch("api.main.load_vectorstore",            return_value=mock_vs), \
         patch("api.main.RAGSystem",                   return_value=mock_rag), \
         patch("api.routes.documents.DOCUMENTS_FOLDER", docs_dir), \
         patch("api.routes.documents.LANCE_DB_PATH",   str(tmp_path / "lance_db")):

        from api.main import app
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c, mock_rag, mock_vs


@pytest.fixture()
def api_client(client):
    c, _, _ = client
    return c


@pytest.fixture()
def api_client_and_rag(client):
    c, mock_rag, _ = client
    return c, mock_rag


@pytest.fixture()
def fake_txt_file():
    content = b"Ceci est un document de test pour le systeme RAG."
    return ("upload.txt", io.BytesIO(content), "text/plain")


@pytest.fixture()
def fake_pdf_file():
    content = b"%PDF-1.4 contenu factice"
    return ("rapport.pdf", io.BytesIO(content), "application/pdf")
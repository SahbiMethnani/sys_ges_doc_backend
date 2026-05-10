# =============================================================
# tests/conftest.py — Fixtures partagées entre tous les tests
# =============================================================
# IMPORTANT : aucun import langchain au niveau module
# pour éviter les erreurs de chargement silencieuses de pytest.
# Tous les imports langchain sont faits DANS les fixtures.
# =============================================================

import os
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# Isolation des chemins LanceDB & documents pour les tests
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def patch_env_paths(tmp_path, monkeypatch):
    """
    Redirige LANCE_DB_PATH et DOCUMENTS_FOLDER vers des dossiers temporaires
    pour chaque test → aucune pollution du projet réel.
    """
    lance_dir = str(tmp_path / "test_lance_db")
    docs_dir  = str(tmp_path / "test_documents")
    os.makedirs(docs_dir, exist_ok=True)

    monkeypatch.setenv("LANCE_DB_PATH",      lance_dir)
    monkeypatch.setenv("DOCUMENTS_FOLDER",   docs_dir)
    monkeypatch.setenv("LANCE_TABLE_NAME",   "documents")
    monkeypatch.setenv("LLM_MODEL",          "mistral")
    monkeypatch.setenv("LLM_BASE_URL",       "http://localhost:11434")
    monkeypatch.setenv("LLM_TEMPERATURE",    "0.1")
    monkeypatch.setenv("EMBEDDING_MODEL",    "sentence-transformers/all-MiniLM-L6-v2")
    monkeypatch.setenv("EMBEDDING_DEVICE",   "cpu")

    yield lance_dir, docs_dir


# ---------------------------------------------------------------------------
# Fixtures : documents LangChain factices
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_documents():
    """Trois documents LangChain minimaux — import différé."""
    from langchain_core.documents import Document
    return [
        Document(page_content="Python est un langage de programmation.",
                 metadata={"source": "doc1.txt"}),
        Document(page_content="LanceDB est une base vectorielle.",
                 metadata={"source": "doc2.txt"}),
        Document(page_content="Les RAG combinent recherche et génération.",
                 metadata={"source": "doc3.txt"}),
    ]


@pytest.fixture()
def sample_txt_file(tmp_path):
    """Crée un vrai fichier .txt dans un dossier temporaire."""
    docs_dir = tmp_path / "documents"
    docs_dir.mkdir()
    f = docs_dir / "hello.txt"
    f.write_text("Bonjour, ceci est un document de test.", encoding="utf-8")
    return str(docs_dir), str(f)


# ---------------------------------------------------------------------------
# Fixtures : mocks des composants lourds (HuggingFace, LanceDB, Ollama)
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_embeddings():
    """Mock léger du modèle d'embeddings."""
    emb = MagicMock()
    emb.embed_documents.side_effect = lambda docs: [[0.1, 0.2, 0.3]] * len(docs)
    emb.embed_query.return_value     = [0.1, 0.2, 0.3]
    return emb


@pytest.fixture()
def mock_llm():
    """Mock du LLM Ollama."""
    llm = MagicMock()
    llm.invoke.return_value = "Réponse simulée du LLM."
    return llm


@pytest.fixture()
def mock_vectorstore(sample_documents):
    """Mock d'un vectorstore LanceDB avec retriever fonctionnel."""
    vs = MagicMock()
    retriever = MagicMock()
    retriever.invoke.return_value = sample_documents[:2]
    vs.as_retriever.return_value  = retriever
    return vs


@pytest.fixture()
def mock_qa_result(sample_documents):
    """Résultat simulé d'un appel RetrievalQA."""
    return {
        "result":           "Python est un langage de programmation.",
        "source_documents": sample_documents[:2],
    }
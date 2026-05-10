# =============================================================
# tests/test_embeddings.py — Tests du module embeddings.py
# =============================================================

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.unit
class TestGetEmbeddings:
    """Tests de la fonction get_embeddings() (modèle HuggingFace mocké)."""

    def test_returns_huggingface_instance(self):
        """get_embeddings() doit retourner un objet HuggingFaceEmbeddings."""
        mock_emb = MagicMock()

        with patch("embeddings.HuggingFaceEmbeddings", return_value=mock_emb) as MockHF:
            from embeddings import get_embeddings
            result = get_embeddings()

        assert result is mock_emb

    def test_called_with_correct_model_name(self):
        """Le nom du modèle doit provenir de la config."""
        mock_emb = MagicMock()

        with patch("embeddings.HuggingFaceEmbeddings", return_value=mock_emb) as MockHF, \
             patch("embeddings.EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"):
            from embeddings import get_embeddings
            get_embeddings()

        call_kwargs = MockHF.call_args.kwargs
        assert call_kwargs["model_name"] == "sentence-transformers/all-MiniLM-L6-v2"

    def test_called_with_correct_device(self):
        """Le device doit provenir de la config (cpu par défaut)."""
        mock_emb = MagicMock()

        with patch("embeddings.HuggingFaceEmbeddings", return_value=mock_emb) as MockHF, \
             patch("embeddings.EMBEDDING_DEVICE", "cpu"):
            from embeddings import get_embeddings
            get_embeddings()

        call_kwargs = MockHF.call_args.kwargs
        assert call_kwargs["model_kwargs"]["device"] == "cpu"

    def test_huggingface_called_once(self):
        """HuggingFaceEmbeddings ne doit être instancié qu'une seule fois."""
        mock_emb = MagicMock()

        with patch("embeddings.HuggingFaceEmbeddings", return_value=mock_emb) as MockHF:
            from embeddings import get_embeddings
            get_embeddings()

        assert MockHF.call_count == 1


@pytest.mark.unit
class TestEmbeddingsInterface:
    """Vérifie que le mock expose l'interface attendue par le reste du projet."""

    def test_mock_embed_query_callable(self, mock_embeddings):
        result = mock_embeddings.embed_query("Bonjour")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_mock_embed_documents_callable(self, mock_embeddings):
        docs = ["doc un", "doc deux"]
        result = mock_embeddings.embed_documents(docs)
        assert isinstance(result, list)
        assert len(result) == len(docs)

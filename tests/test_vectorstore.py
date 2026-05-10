# =============================================================
# tests/test_vectorstore.py — Tests du module vectorstore.py
# =============================================================

import os
from unittest.mock import MagicMock, patch, PropertyMock

import pytest
from langchain_core.documents import Document


# ---------------------------------------------------------------------------
# Tests : vector_index_exists()
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestVectorIndexExists:
    """Tests de la fonction vector_index_exists()."""

    def test_returns_false_when_no_directory(self, tmp_path):
        """Aucun dossier LanceDB → False."""
        with patch("vectorstore.LANCE_DB_PATH", str(tmp_path / "missing")):
            from vectorstore import vector_index_exists
            assert vector_index_exists() is False

    def test_returns_false_when_table_absent(self, tmp_path):
        """Dossier présent mais table absente → False."""
        lance_dir = tmp_path / "lance_db"
        lance_dir.mkdir()

        mock_conn = MagicMock()
        mock_conn.table_names.return_value = []  # table absente

        with patch("vectorstore.LANCE_DB_PATH", str(lance_dir)), \
             patch("vectorstore.LANCE_TABLE_NAME", "documents"), \
             patch("lancedb.connect", return_value=mock_conn):
            from vectorstore import vector_index_exists
            assert vector_index_exists() is False

    def test_returns_true_when_table_present(self, tmp_path):
        """Dossier + table présents → True."""
        lance_dir = tmp_path / "lance_db"
        lance_dir.mkdir()

        mock_conn = MagicMock()
        mock_conn.table_names.return_value = ["documents"]

        with patch("vectorstore.LANCE_DB_PATH", str(lance_dir)), \
             patch("vectorstore.LANCE_TABLE_NAME", "documents"), \
             patch("lancedb.connect", return_value=mock_conn):
            from vectorstore import vector_index_exists
            assert vector_index_exists() is True

    def test_returns_false_on_os_error(self, tmp_path):
        """OSError lors de la connexion → False (pas d'exception levée)."""
        lance_dir = tmp_path / "lance_db"
        lance_dir.mkdir()

        with patch("vectorstore.LANCE_DB_PATH", str(lance_dir)), \
             patch("lancedb.connect", side_effect=OSError("permission denied")):
            from vectorstore import vector_index_exists
            assert vector_index_exists() is False


# ---------------------------------------------------------------------------
# Tests : build_vectorstore()
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestBuildVectorstore:
    """Tests de la fonction build_vectorstore()."""

    def test_returns_lancedb_instance(self, sample_documents, mock_embeddings, tmp_path):
        """build_vectorstore doit retourner un objet non-None."""
        mock_vs = MagicMock()

        with patch("vectorstore.LANCE_DB_PATH", str(tmp_path / "db")), \
             patch("lancedb.connect") as mock_connect, \
             patch("vectorstore.LanceDB.from_documents", return_value=mock_vs):
            from vectorstore import build_vectorstore
            result = build_vectorstore(sample_documents, mock_embeddings)

        assert result is mock_vs

    def test_from_documents_called_with_chunks(self, sample_documents, mock_embeddings, tmp_path):
        """from_documents doit être appelé avec des chunks et l'embedding."""
        mock_vs = MagicMock()

        with patch("vectorstore.LANCE_DB_PATH", str(tmp_path / "db")), \
             patch("lancedb.connect"), \
             patch("vectorstore.LanceDB.from_documents", return_value=mock_vs) as mock_from:
            from vectorstore import build_vectorstore
            build_vectorstore(sample_documents, mock_embeddings)

        assert mock_from.called
        call_kwargs = mock_from.call_args.kwargs
        assert call_kwargs["embedding"] is mock_embeddings

    def test_mode_overwrite_used(self, sample_documents, mock_embeddings, tmp_path):
        """Le mode 'overwrite' doit toujours être utilisé."""
        mock_vs = MagicMock()

        with patch("vectorstore.LANCE_DB_PATH", str(tmp_path / "db")), \
             patch("lancedb.connect"), \
             patch("vectorstore.LanceDB.from_documents", return_value=mock_vs) as mock_from:
            from vectorstore import build_vectorstore
            build_vectorstore(sample_documents, mock_embeddings)

        call_kwargs = mock_from.call_args.kwargs
        assert call_kwargs.get("mode") == "overwrite"

    def test_empty_documents_list(self, mock_embeddings, tmp_path):
        """build_vectorstore avec liste vide ne doit pas lever d'exception."""
        mock_vs = MagicMock()

        with patch("vectorstore.LANCE_DB_PATH", str(tmp_path / "db")), \
             patch("lancedb.connect"), \
             patch("vectorstore.LanceDB.from_documents", return_value=mock_vs):
            from vectorstore import build_vectorstore
            result = build_vectorstore([], mock_embeddings)

        assert result is mock_vs


# ---------------------------------------------------------------------------
# Tests : load_vectorstore()
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestLoadVectorstore:
    """Tests de la fonction load_vectorstore()."""

    def test_raises_when_table_missing(self, mock_embeddings, tmp_path):
        """FileNotFoundError si la table n'existe pas."""
        mock_conn = MagicMock()
        mock_conn.table_names.return_value = []  # table absente

        with patch("vectorstore.LANCE_DB_PATH", str(tmp_path / "db")), \
             patch("vectorstore.LANCE_TABLE_NAME", "documents"), \
             patch("lancedb.connect", return_value=mock_conn):
            from vectorstore import load_vectorstore
            with pytest.raises(FileNotFoundError):
                load_vectorstore(mock_embeddings)

    def test_returns_lancedb_when_table_present(self, mock_embeddings, tmp_path):
        """Retourne un LanceDB si la table existe."""
        mock_conn = MagicMock()
        mock_conn.table_names.return_value = ["documents"]
        mock_vs = MagicMock()

        with patch("vectorstore.LANCE_DB_PATH", str(tmp_path / "db")), \
             patch("vectorstore.LANCE_TABLE_NAME", "documents"), \
             patch("lancedb.connect", return_value=mock_conn), \
             patch("vectorstore.LanceDB", return_value=mock_vs):
            from vectorstore import load_vectorstore
            result = load_vectorstore(mock_embeddings)

        assert result is mock_vs

# =============================================================
# tests/test_main.py — Tests de la logique d'orchestration (main.py)
# =============================================================

import os
from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.unit
class TestSetupVectorstore:
    """Tests de setup_vectorstore() sans I/O réelle."""

    def test_returns_none_when_docs_folder_missing(self, tmp_path):
        """Dossier documents absent → None (et création du dossier)."""
        missing = str(tmp_path / "missing_docs")

        with patch("main.DOCUMENTS_FOLDER", missing), \
             patch("main.vector_index_exists", return_value=False):
            from main import setup_vectorstore
            result = setup_vectorstore(MagicMock())

        assert result is None
        assert os.path.isdir(missing)  # le dossier doit être créé

    def test_returns_none_when_no_documents_found(self, tmp_path):
        """Dossier vide → None."""
        docs_dir = str(tmp_path / "empty_docs")
        os.makedirs(docs_dir)

        with patch("main.DOCUMENTS_FOLDER", docs_dir), \
             patch("main.vector_index_exists", return_value=False), \
             patch("main.load_documents", return_value=[]):
            from main import setup_vectorstore
            result = setup_vectorstore(MagicMock())

        assert result is None

    def test_builds_vectorstore_when_documents_found(self, tmp_path, sample_documents):
        """Des documents présents → build_vectorstore appelé."""
        docs_dir = str(tmp_path / "docs")
        os.makedirs(docs_dir)
        mock_vs = MagicMock()

        with patch("main.DOCUMENTS_FOLDER", docs_dir), \
             patch("main.vector_index_exists", return_value=False), \
             patch("main.load_documents", return_value=sample_documents), \
             patch("main.build_vectorstore", return_value=mock_vs) as mock_build:
            from main import setup_vectorstore
            result = setup_vectorstore(MagicMock())

        assert result is mock_vs
        mock_build.assert_called_once()

    def test_loads_existing_vectorstore_when_user_chooses_2(self, tmp_path, sample_documents):
        """Choix '2' de l'utilisateur → load_vectorstore (pas de rebuild)."""
        docs_dir = str(tmp_path / "docs")
        os.makedirs(docs_dir)
        mock_vs = MagicMock()

        with patch("main.DOCUMENTS_FOLDER", docs_dir), \
             patch("main.vector_index_exists", return_value=True), \
             patch("builtins.input", return_value="2"), \
             patch("main.load_vectorstore", return_value=mock_vs) as mock_load:
            from main import setup_vectorstore
            result = setup_vectorstore(MagicMock())

        assert result is mock_vs
        mock_load.assert_called_once()

    def test_rebuilds_vectorstore_when_user_chooses_1(self, tmp_path, sample_documents):
        """Choix '1' → suppression + rebuild."""
        docs_dir = str(tmp_path / "docs")
        os.makedirs(docs_dir)
        mock_vs = MagicMock()

        with patch("main.DOCUMENTS_FOLDER", docs_dir), \
             patch("main.vector_index_exists", return_value=True), \
             patch("builtins.input", return_value="1"), \
             patch("main.shutil.rmtree") as mock_rm, \
             patch("main.load_documents", return_value=sample_documents), \
             patch("main.build_vectorstore", return_value=mock_vs) as mock_build:
            from main import setup_vectorstore
            result = setup_vectorstore(MagicMock())

        mock_rm.assert_called_once()
        mock_build.assert_called_once()
        assert result is mock_vs


@pytest.mark.unit
class TestInteractiveLoop:
    """Tests de la boucle REPL interactive."""

    def _make_rag(self, mock_qa_result):
        rag = MagicMock()
        rag.query.return_value = mock_qa_result
        return rag

    def test_quit_exits_loop(self, mock_qa_result):
        rag = self._make_rag(mock_qa_result)
        with patch("builtins.input", return_value="quit"):
            from main import interactive_loop
            interactive_loop(rag)
        rag.query.assert_not_called()

    def test_exit_exits_loop(self, mock_qa_result):
        rag = self._make_rag(mock_qa_result)
        with patch("builtins.input", return_value="exit"):
            from main import interactive_loop
            interactive_loop(rag)
        rag.query.assert_not_called()

    def test_q_exits_loop(self, mock_qa_result):
        rag = self._make_rag(mock_qa_result)
        with patch("builtins.input", return_value="q"):
            from main import interactive_loop
            interactive_loop(rag)
        rag.query.assert_not_called()

    def test_question_triggers_rag_query(self, mock_qa_result):
        """Une vraie question → rag.query() appelé, puis 'quit'."""
        rag = self._make_rag(mock_qa_result)
        responses = iter(["Qu'est-ce que Python ?", "quit"])
        with patch("builtins.input", side_effect=responses):
            from main import interactive_loop
            interactive_loop(rag)
        rag.query.assert_called_once_with("Qu'est-ce que Python ?", show_sources=True)

    def test_empty_input_skipped(self, mock_qa_result):
        """Entrée vide → rag.query() non appelé."""
        rag = self._make_rag(mock_qa_result)
        responses = iter(["", "quit"])
        with patch("builtins.input", side_effect=responses):
            from main import interactive_loop
            interactive_loop(rag)
        rag.query.assert_not_called()

    def test_exception_in_query_does_not_crash_loop(self, mock_qa_result):
        """Exception dans rag.query() → la boucle continue."""
        rag = MagicMock()
        rag.query.side_effect = RuntimeError("LLM HS")
        responses = iter(["Question qui plante", "quit"])
        with patch("builtins.input", side_effect=responses):
            from main import interactive_loop
            interactive_loop(rag)  # ne doit pas lever d'exception

# =============================================================
# tests/test_rag.py — Tests du module rag.py
# =============================================================

from unittest.mock import MagicMock, patch, call

import pytest
from langchain_core.documents import Document

from rag import RAGSystem, chunk_document_source


# ---------------------------------------------------------------------------
# Tests : chunk_document_source()
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestChunkDocumentSource:
    """Tests de la fonction utilitaire chunk_document_source()."""

    def test_returns_source_from_metadata(self):
        doc = Document(page_content="contenu", metadata={"source": "mon_fichier.pdf"})
        assert chunk_document_source(doc) == "mon_fichier.pdf"

    def test_returns_source_from_nested_metadata(self):
        """LanceDB imbrique parfois les métadonnées dans metadata['metadata']."""
        doc = Document(
            page_content="contenu",
            metadata={"metadata": {"source": "nested_file.txt"}},
        )
        assert chunk_document_source(doc) == "nested_file.txt"

    def test_returns_inconnu_when_no_source(self):
        doc = Document(page_content="contenu", metadata={})
        assert chunk_document_source(doc) == "Inconnu"

    def test_returns_inconnu_when_source_empty_string(self):
        doc = Document(page_content="contenu", metadata={"source": ""})
        assert chunk_document_source(doc) == "Inconnu"

    def test_returns_inconnu_when_metadata_none(self):
        doc = Document(page_content="contenu", metadata={})
        doc.metadata = None  # cas extrême
        assert chunk_document_source(doc) == "Inconnu"

    def test_prefers_root_source_over_nested(self):
        """La clé 'source' à la racine doit avoir priorité sur la nested."""
        doc = Document(
            page_content="contenu",
            metadata={
                "source": "root.txt",
                "metadata": {"source": "nested.txt"},
            },
        )
        assert chunk_document_source(doc) == "root.txt"

    def test_handles_non_string_source(self):
        """Une source non-string doit retourner 'Inconnu'."""
        doc = Document(page_content="contenu", metadata={"source": 42})
        assert chunk_document_source(doc) == "Inconnu"


# ---------------------------------------------------------------------------
# Tests : RAGSystem.__init__()
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestRAGSystemInit:
    """Tests de l'initialisation de RAGSystem."""

    def test_init_stores_vectorstore(self, mock_vectorstore, mock_llm):
        rag = RAGSystem(vectorstore=mock_vectorstore, llm=mock_llm)
        assert rag.vectorstore is mock_vectorstore

    def test_init_stores_llm(self, mock_vectorstore, mock_llm):
        rag = RAGSystem(vectorstore=mock_vectorstore, llm=mock_llm)
        assert rag.llm is mock_llm

    def test_qa_chain_initially_none(self, mock_vectorstore, mock_llm):
        rag = RAGSystem(vectorstore=mock_vectorstore, llm=mock_llm)
        assert rag._qa_chain is None


# ---------------------------------------------------------------------------
# Tests : RAGSystem.qa_chain (lazy init)
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestRAGSystemQAChain:
    """Tests de la propriété qa_chain (lazy initialization)."""

    def test_qa_chain_built_on_first_access(self, mock_vectorstore, mock_llm):
        rag = RAGSystem(vectorstore=mock_vectorstore, llm=mock_llm)
        mock_chain = MagicMock()

        with patch.object(rag, "_build_qa_chain", return_value=mock_chain):
            chain = rag.qa_chain

        assert chain is mock_chain

    def test_qa_chain_not_rebuilt_on_second_access(self, mock_vectorstore, mock_llm):
        rag = RAGSystem(vectorstore=mock_vectorstore, llm=mock_llm)
        mock_chain = MagicMock()

        with patch.object(rag, "_build_qa_chain", return_value=mock_chain) as mock_build:
            _ = rag.qa_chain
            _ = rag.qa_chain  # second accès

        # _build_qa_chain ne doit être appelé qu'une seule fois
        assert mock_build.call_count == 1

    def test_reset_qa_chain_forces_rebuild(self, mock_vectorstore, mock_llm):
        rag = RAGSystem(vectorstore=mock_vectorstore, llm=mock_llm)
        mock_chain = MagicMock()

        with patch.object(rag, "_build_qa_chain", return_value=mock_chain) as mock_build:
            _ = rag.qa_chain
            rag.reset_qa_chain()
            _ = rag.qa_chain  # doit reconstruire

        assert mock_build.call_count == 2


# ---------------------------------------------------------------------------
# Tests : RAGSystem.query()
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestRAGSystemQuery:
    """Tests de la méthode query()."""

    def _make_rag_with_mock_chain(self, mock_vectorstore, mock_llm, qa_result):
        """Helper : construit un RAGSystem avec une chaîne QA mockée."""
        rag = RAGSystem(vectorstore=mock_vectorstore, llm=mock_llm)
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = qa_result
        rag._qa_chain = mock_chain
        return rag, mock_chain

    def test_query_returns_dict(self, mock_vectorstore, mock_llm, mock_qa_result):
        rag, _ = self._make_rag_with_mock_chain(mock_vectorstore, mock_llm, mock_qa_result)
        result = rag.query("Qu'est-ce que Python ?", show_sources=False)
        assert isinstance(result, dict)

    def test_query_contains_result_key(self, mock_vectorstore, mock_llm, mock_qa_result):
        rag, _ = self._make_rag_with_mock_chain(mock_vectorstore, mock_llm, mock_qa_result)
        result = rag.query("Qu'est-ce que Python ?", show_sources=False)
        assert "result" in result

    def test_query_contains_source_documents(self, mock_vectorstore, mock_llm, mock_qa_result):
        rag, _ = self._make_rag_with_mock_chain(mock_vectorstore, mock_llm, mock_qa_result)
        result = rag.query("Test", show_sources=False)
        assert "source_documents" in result
        assert len(result["source_documents"]) > 0

    def test_query_invokes_chain_with_correct_key(self, mock_vectorstore, mock_llm, mock_qa_result):
        rag, mock_chain = self._make_rag_with_mock_chain(mock_vectorstore, mock_llm, mock_qa_result)
        question = "Qu'est-ce que LanceDB ?"
        rag.query(question, show_sources=False)
        mock_chain.invoke.assert_called_once_with({"query": question})

    def test_query_show_sources_false_no_error(self, mock_vectorstore, mock_llm, mock_qa_result):
        """show_sources=False ne doit lever aucune exception."""
        rag, _ = self._make_rag_with_mock_chain(mock_vectorstore, mock_llm, mock_qa_result)
        rag.query("Test sources masquées", show_sources=False)  # pas d'exception

    def test_query_show_sources_true_no_error(self, mock_vectorstore, mock_llm, mock_qa_result):
        """show_sources=True ne doit lever aucune exception non plus."""
        rag, _ = self._make_rag_with_mock_chain(mock_vectorstore, mock_llm, mock_qa_result)
        rag.query("Test sources affichées", show_sources=True)

    def test_query_propagates_exception(self, mock_vectorstore, mock_llm):
        """Une exception du LLM doit remonter jusqu'à l'appelant."""
        rag = RAGSystem(vectorstore=mock_vectorstore, llm=mock_llm)
        mock_chain = MagicMock()
        mock_chain.invoke.side_effect = RuntimeError("LLM indisponible")
        rag._qa_chain = mock_chain

        with pytest.raises(RuntimeError, match="LLM indisponible"):
            rag.query("Question impossible", show_sources=False)


# ---------------------------------------------------------------------------
# Tests : RAGSystem._build_qa_chain()
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestBuildQAChain:
    """Tests de la construction interne de la chaîne QA."""

    def test_build_uses_retriever(self, mock_vectorstore, mock_llm):
        """as_retriever doit être appelé lors de la construction de la chaîne."""
        with patch("rag.RetrievalQA.from_chain_type") as mock_qa_cls:
            mock_qa_cls.return_value = MagicMock()
            rag = RAGSystem(vectorstore=mock_vectorstore, llm=mock_llm)
            _ = rag.qa_chain

        mock_vectorstore.as_retriever.assert_called_once()

    def test_build_passes_llm(self, mock_vectorstore, mock_llm):
        """Le LLM doit être transmis à RetrievalQA."""
        with patch("rag.RetrievalQA.from_chain_type") as mock_qa_cls:
            mock_qa_cls.return_value = MagicMock()
            rag = RAGSystem(vectorstore=mock_vectorstore, llm=mock_llm)
            _ = rag.qa_chain

        call_kwargs = mock_qa_cls.call_args.kwargs
        assert call_kwargs.get("llm") is mock_llm

    def test_build_return_source_documents_true(self, mock_vectorstore, mock_llm):
        """return_source_documents doit être True."""
        with patch("rag.RetrievalQA.from_chain_type") as mock_qa_cls:
            mock_qa_cls.return_value = MagicMock()
            rag = RAGSystem(vectorstore=mock_vectorstore, llm=mock_llm)
            _ = rag.qa_chain

        call_kwargs = mock_qa_cls.call_args.kwargs
        assert call_kwargs.get("return_source_documents") is True

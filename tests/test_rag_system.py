import os
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest
from langchain_core.documents import Document


# ===========================================================================
# Fixtures locales
# ===========================================================================

@pytest.fixture()
def mock_hf_embeddings():
    emb = MagicMock()
    emb.embed_query.return_value = [0.1, 0.2, 0.3]
    emb.embed_documents.side_effect = lambda docs: [[0.1, 0.2, 0.3]] * len(docs)
    return emb


@pytest.fixture()
def mock_ollama():
    llm = MagicMock()
    llm.invoke.return_value = "Réponse simulée."
    return llm


@pytest.fixture()
def mock_lancedb_conn():
    conn = MagicMock()
    conn.table_names.return_value = []
    return conn


@pytest.fixture()
def sample_docs():
    return [
        Document(page_content="Python est un langage de programmation.",
                 metadata={"source": "doc1.txt"}),
        Document(page_content="LanceDB est une base vectorielle columnar.",
                 metadata={"source": "doc2.txt"}),
        Document(page_content="Le RAG améliore les LLMs avec de la recherche.",
                 metadata={"source": "doc3.txt"}),
    ]


@pytest.fixture()
def rag_system(tmp_path, mock_hf_embeddings, mock_ollama):
    """
    Instance de RAGSystem avec embeddings et LLM mockés.
    Aucun modèle n'est réellement chargé.
    """
    with patch("rag_system.HuggingFaceEmbeddings", return_value=mock_hf_embeddings), \
         patch("rag_system.Ollama",                return_value=mock_ollama):
        from rag_system import RAGSystem
        rag = RAGSystem(
            persist_directory=str(tmp_path / "lance_db"),
            table_name="documents",
            model_name="mistral",
        )
    return rag


# ===========================================================================
# Tests : __init__()
# ===========================================================================

@pytest.mark.unit
class TestRAGSystemInit:
    """Tests de l'initialisation de RAGSystem."""

    def test_persist_directory_stored(self, tmp_path, mock_hf_embeddings, mock_ollama):
        with patch("rag_system.HuggingFaceEmbeddings", return_value=mock_hf_embeddings), \
             patch("rag_system.Ollama",                return_value=mock_ollama):
            from rag_system import RAGSystem
            rag = RAGSystem(persist_directory=str(tmp_path / "db"))
        assert str(tmp_path / "db") in rag.persist_directory

    def test_table_name_stored(self, rag_system):
        assert rag_system.table_name == "documents"

    def test_model_name_stored(self, rag_system):
        assert rag_system.model_name == "mistral"

    def test_embeddings_initialized(self, rag_system, mock_hf_embeddings):
        assert rag_system.embeddings is mock_hf_embeddings

    def test_llm_initialized(self, rag_system, mock_ollama):
        assert rag_system.llm is mock_ollama

    def test_vectorstore_initially_none(self, rag_system):
        assert rag_system.vectorstore is None

    def test_text_splitter_initialized(self, rag_system):
        assert rag_system.text_splitter is not None

    def test_huggingface_called_with_correct_model(self, tmp_path, mock_ollama):
        with patch("rag_system.HuggingFaceEmbeddings") as MockHF, \
             patch("rag_system.Ollama", return_value=mock_ollama):
            MockHF.return_value = MagicMock()
            from rag_system import RAGSystem
            RAGSystem(persist_directory=str(tmp_path / "db"), model_name="mistral")
        call_kwargs = MockHF.call_args.kwargs
        assert call_kwargs["model_name"] == "sentence-transformers/all-MiniLM-L6-v2"
        assert call_kwargs["model_kwargs"]["device"] == "cpu"

    def test_ollama_called_with_correct_model(self, tmp_path, mock_hf_embeddings):
        with patch("rag_system.HuggingFaceEmbeddings", return_value=mock_hf_embeddings), \
             patch("rag_system.Ollama") as MockOllama:
            MockOllama.return_value = MagicMock()
            from rag_system import RAGSystem
            RAGSystem(persist_directory=str(tmp_path / "db"), model_name="llama2")
        call_kwargs = MockOllama.call_args.kwargs
        assert call_kwargs["model"] == "llama2"


# ===========================================================================
# Tests : load_documents()
# ===========================================================================

@pytest.mark.unit
class TestLoadDocuments:
    """Tests de la méthode load_documents()."""

    def test_returns_empty_list_when_folder_missing(self, rag_system, tmp_path):
        result = rag_system.load_documents(str(tmp_path / "inexistant"))
        assert isinstance(result, list)
        assert len(result) == 0

    def test_returns_empty_list_when_folder_empty(self, rag_system, tmp_path):
        empty = tmp_path / "empty"
        empty.mkdir()
        result = rag_system.load_documents(str(empty))
        assert result == []

    def test_ignores_unsupported_extensions(self, rag_system, tmp_path):
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "data.csv").write_text("a,b,c")
        (docs_dir / "config.json").write_text('{"key": "value"}')
        result = rag_system.load_documents(str(docs_dir))
        assert result == []

    def test_loads_txt_file(self, rag_system, tmp_path):
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "note.txt").write_text("Contenu de test.", encoding="utf-8")
        result = rag_system.load_documents(str(docs_dir))
        assert len(result) >= 1
        assert all(isinstance(d, Document) for d in result)

    def test_loads_raw_file(self, rag_system, tmp_path):
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "dump.raw").write_text("raw content", encoding="utf-8")
        result = rag_system.load_documents(str(docs_dir))
        assert len(result) >= 1

    def test_loads_multiple_txt_files(self, rag_system, tmp_path):
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        for i in range(3):
            (docs_dir / f"doc{i}.txt").write_text(f"Document {i}", encoding="utf-8")
        result = rag_system.load_documents(str(docs_dir))
        assert len(result) >= 3

    def test_loads_pdf_via_loader(self, rag_system, tmp_path):
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "report.pdf").write_bytes(b"%PDF-1.4 fake")

        fake_doc = Document(page_content="Contenu PDF.", metadata={"source": "report.pdf"})
        with patch("rag_system.PyPDFLoader") as MockPDF:
            MockPDF.return_value.load.return_value = [fake_doc]
            result = rag_system.load_documents(str(docs_dir))
        assert len(result) >= 1

    def test_loads_html_via_loader(self, rag_system, tmp_path):
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "page.html").write_text("<html><body>Test</body></html>", encoding="utf-8")

        fake_doc = Document(page_content="Test", metadata={"source": "page.html"})
        with patch("rag_system.UnstructuredHTMLLoader") as MockHTML:
            MockHTML.return_value.load.return_value = [fake_doc]
            result = rag_system.load_documents(str(docs_dir))
        assert len(result) >= 1

    def test_skips_corrupt_file_and_continues(self, rag_system, tmp_path):
        """Un fichier corrompu ne doit pas interrompre le chargement des autres."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "bad.txt").write_bytes(b"\xff\xfe invalid")
        (docs_dir / "good.txt").write_text("Contenu valide.", encoding="utf-8")
        result = rag_system.load_documents(str(docs_dir))
        assert any("Contenu valide" in d.page_content for d in result)

    def test_source_metadata_present(self, rag_system, tmp_path):
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "meta.txt").write_text("Texte avec source.", encoding="utf-8")
        result = rag_system.load_documents(str(docs_dir))
        assert "source" in result[0].metadata


# ===========================================================================
# Tests : process_documents()
# ===========================================================================

@pytest.mark.unit
class TestProcessDocuments:
    """Tests de la méthode process_documents()."""

    def test_sets_vectorstore(self, rag_system, sample_docs, tmp_path):
        mock_vs = MagicMock()
        with patch("rag_system.lancedb.connect"), \
             patch("rag_system.LanceDB.from_documents", return_value=mock_vs):
            rag_system.process_documents(sample_docs)
        assert rag_system.vectorstore is mock_vs

    def test_from_documents_called_with_embedding(self, rag_system, sample_docs):
        mock_vs = MagicMock()
        with patch("rag_system.lancedb.connect"), \
             patch("rag_system.LanceDB.from_documents", return_value=mock_vs) as mock_from:
            rag_system.process_documents(sample_docs)
        call_kwargs = mock_from.call_args.kwargs
        assert call_kwargs["embedding"] is rag_system.embeddings

    def test_mode_overwrite_used(self, rag_system, sample_docs):
        mock_vs = MagicMock()
        with patch("rag_system.lancedb.connect"), \
             patch("rag_system.LanceDB.from_documents", return_value=mock_vs) as mock_from:
            rag_system.process_documents(sample_docs)
        call_kwargs = mock_from.call_args.kwargs
        assert call_kwargs.get("mode") == "overwrite"

    def test_table_name_passed(self, rag_system, sample_docs):
        mock_vs = MagicMock()
        with patch("rag_system.lancedb.connect"), \
             patch("rag_system.LanceDB.from_documents", return_value=mock_vs) as mock_from:
            rag_system.process_documents(sample_docs)
        call_kwargs = mock_from.call_args.kwargs
        assert call_kwargs.get("table_name") == "documents"

    def test_text_splitter_produces_chunks(self, rag_system, sample_docs):
        """Le text_splitter doit découper les documents en chunks."""
        mock_vs = MagicMock()
        with patch("rag_system.lancedb.connect"), \
             patch("rag_system.LanceDB.from_documents", return_value=mock_vs) as mock_from:
            rag_system.process_documents(sample_docs)
        # Les chunks transmis doivent être des Documents
        chunks_arg = mock_from.call_args.kwargs.get("documents") or \
                     mock_from.call_args.args[0] if mock_from.call_args.args else []
        if chunks_arg:
            assert all(isinstance(c, Document) for c in chunks_arg)

    def test_empty_documents_list_does_not_raise(self, rag_system):
        mock_vs = MagicMock()
        with patch("rag_system.lancedb.connect"), \
             patch("rag_system.LanceDB.from_documents", return_value=mock_vs):
            rag_system.process_documents([])  # ne doit pas lever d'exception


# ===========================================================================
# Tests : load_existing_vectorstore()
# ===========================================================================

@pytest.mark.unit
class TestLoadExistingVectorstore:
    """Tests de la méthode load_existing_vectorstore()."""

    def test_raises_when_table_missing(self, rag_system):
        mock_conn = MagicMock()
        mock_conn.table_names.return_value = []
        with patch("rag_system.lancedb.connect", return_value=mock_conn):
            with pytest.raises(FileNotFoundError):
                rag_system.load_existing_vectorstore()

    def test_sets_vectorstore_when_table_present(self, rag_system):
        mock_conn = MagicMock()
        mock_conn.table_names.return_value = ["documents"]
        mock_vs = MagicMock()
        with patch("rag_system.lancedb.connect", return_value=mock_conn), \
             patch("rag_system.LanceDB", return_value=mock_vs):
            rag_system.load_existing_vectorstore()
        assert rag_system.vectorstore is mock_vs

    def test_error_message_contains_table_name(self, rag_system):
        mock_conn = MagicMock()
        mock_conn.table_names.return_value = []
        with patch("rag_system.lancedb.connect", return_value=mock_conn):
            with pytest.raises(FileNotFoundError, match="documents"):
                rag_system.load_existing_vectorstore()

    def test_lancedb_called_with_correct_embedding(self, rag_system):
        mock_conn = MagicMock()
        mock_conn.table_names.return_value = ["documents"]
        mock_vs = MagicMock()
        with patch("rag_system.lancedb.connect", return_value=mock_conn), \
             patch("rag_system.LanceDB", return_value=mock_vs) as MockLDB:
            rag_system.load_existing_vectorstore()
        call_kwargs = MockLDB.call_args.kwargs
        assert call_kwargs.get("embedding") is rag_system.embeddings


# ===========================================================================
# Tests : create_qa_chain()
# ===========================================================================

@pytest.mark.unit
class TestCreateQAChain:
    """Tests de la méthode create_qa_chain()."""

    def test_raises_when_no_vectorstore(self, rag_system):
        """Doit lever ValueError si vectorstore est None."""
        assert rag_system.vectorstore is None
        with pytest.raises(ValueError):
            rag_system.create_qa_chain()

    def test_returns_chain_when_vectorstore_set(self, rag_system):
        rag_system.vectorstore = MagicMock()
        mock_chain = MagicMock()
        with patch("rag_system.RetrievalQA.from_chain_type", return_value=mock_chain):
            chain = rag_system.create_qa_chain()
        assert chain is mock_chain

    def test_uses_as_retriever(self, rag_system):
        mock_vs = MagicMock()
        rag_system.vectorstore = mock_vs
        with patch("rag_system.RetrievalQA.from_chain_type", return_value=MagicMock()):
            rag_system.create_qa_chain()
        mock_vs.as_retriever.assert_called_once()

    def test_return_source_documents_true(self, rag_system):
        rag_system.vectorstore = MagicMock()
        with patch("rag_system.RetrievalQA.from_chain_type") as mock_qa:
            mock_qa.return_value = MagicMock()
            rag_system.create_qa_chain()
        call_kwargs = mock_qa.call_args.kwargs
        assert call_kwargs.get("return_source_documents") is True

    def test_passes_llm_to_chain(self, rag_system):
        rag_system.vectorstore = MagicMock()
        with patch("rag_system.RetrievalQA.from_chain_type") as mock_qa:
            mock_qa.return_value = MagicMock()
            rag_system.create_qa_chain()
        call_kwargs = mock_qa.call_args.kwargs
        assert call_kwargs.get("llm") is rag_system.llm

    def test_top_k_is_3(self, rag_system):
        """Le retriever doit chercher les 3 chunks les plus pertinents."""
        mock_vs = MagicMock()
        rag_system.vectorstore = mock_vs
        with patch("rag_system.RetrievalQA.from_chain_type", return_value=MagicMock()):
            rag_system.create_qa_chain()
        call_kwargs = mock_vs.as_retriever.call_args.kwargs
        assert call_kwargs.get("search_kwargs", {}).get("k") == 3

    def test_prompt_template_contains_context_and_question(self, rag_system):
        """Le prompt doit contenir les placeholders {context} et {question}."""
        rag_system.vectorstore = MagicMock()
        with patch("rag_system.RetrievalQA.from_chain_type") as mock_qa:
            mock_qa.return_value = MagicMock()
            rag_system.create_qa_chain()
        chain_type_kwargs = mock_qa.call_args.kwargs.get("chain_type_kwargs", {})
        prompt = chain_type_kwargs.get("prompt")
        if prompt is not None:
            assert "{context}" in prompt.template
            assert "{question}" in prompt.template


# ===========================================================================
# Tests : query()
# ===========================================================================

@pytest.mark.unit
class TestQuery:
    """Tests de la méthode query()."""

    def _setup_rag(self, rag_system, sample_docs):
        """Configure un RAGSystem prêt à répondre."""
        mock_chain = MagicMock()
        mock_chain.return_value = {
            "result": "Python est un langage de programmation.",
            "source_documents": sample_docs[:2],
        }
        rag_system.vectorstore = MagicMock()
        return mock_chain

    def test_query_returns_dict(self, rag_system, sample_docs):
        mock_chain = self._setup_rag(rag_system, sample_docs)
        with patch.object(rag_system, "create_qa_chain", return_value=mock_chain):
            result = rag_system.query("Qu'est-ce que Python ?", show_sources=False)
        assert isinstance(result, dict)

    def test_query_contains_result_key(self, rag_system, sample_docs):
        mock_chain = self._setup_rag(rag_system, sample_docs)
        with patch.object(rag_system, "create_qa_chain", return_value=mock_chain):
            result = rag_system.query("Test", show_sources=False)
        assert "result" in result

    def test_query_contains_source_documents(self, rag_system, sample_docs):
        mock_chain = self._setup_rag(rag_system, sample_docs)
        with patch.object(rag_system, "create_qa_chain", return_value=mock_chain):
            result = rag_system.query("Test", show_sources=False)
        assert "source_documents" in result
        assert len(result["source_documents"]) > 0

    def test_query_passes_question_correctly(self, rag_system, sample_docs):
        mock_chain = self._setup_rag(rag_system, sample_docs)
        with patch.object(rag_system, "create_qa_chain", return_value=mock_chain):
            rag_system.query("Qu'est-ce que LanceDB ?", show_sources=False)
        mock_chain.assert_called_once_with({"query": "Qu'est-ce que LanceDB ?"})

    def test_query_calls_create_qa_chain(self, rag_system, sample_docs):
        mock_chain = self._setup_rag(rag_system, sample_docs)
        with patch.object(rag_system, "create_qa_chain", return_value=mock_chain) as mock_create:
            rag_system.query("Question test", show_sources=False)
        mock_create.assert_called_once()

    def test_query_show_sources_false_no_error(self, rag_system, sample_docs):
        mock_chain = self._setup_rag(rag_system, sample_docs)
        with patch.object(rag_system, "create_qa_chain", return_value=mock_chain):
            rag_system.query("Test sans sources", show_sources=False)

    def test_query_show_sources_true_no_error(self, rag_system, sample_docs):
        mock_chain = self._setup_rag(rag_system, sample_docs)
        with patch.object(rag_system, "create_qa_chain", return_value=mock_chain):
            rag_system.query("Test avec sources", show_sources=True)

    def test_query_raises_when_chain_fails(self, rag_system, sample_docs):
        """Une exception dans la chaîne QA doit remonter."""
        rag_system.vectorstore = MagicMock()
        mock_chain = MagicMock()
        mock_chain.side_effect = RuntimeError("LLM indisponible")
        with patch.object(rag_system, "create_qa_chain", return_value=mock_chain):
            with pytest.raises(RuntimeError, match="LLM indisponible"):
                rag_system.query("Question impossible", show_sources=False)

    def test_query_result_is_string(self, rag_system, sample_docs):
        mock_chain = self._setup_rag(rag_system, sample_docs)
        with patch.object(rag_system, "create_qa_chain", return_value=mock_chain):
            result = rag_system.query("Test", show_sources=False)
        assert isinstance(result["result"], str)

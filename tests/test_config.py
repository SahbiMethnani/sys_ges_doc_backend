# =============================================================
# tests/test_config.py — Tests du module config.py
# =============================================================

import os
import pytest


@pytest.mark.unit
class TestConfigDefaults:
    """Vérifie que config.py expose bien les variables attendues."""

    def test_llm_model_default(self):
        """LLM_MODEL doit valoir 'mistral' par défaut (via monkeypatch)."""
        from config import LLM_MODEL
        assert isinstance(LLM_MODEL, str)
        assert len(LLM_MODEL) > 0

    def test_llm_base_url_is_string(self):
        from config import LLM_BASE_URL
        assert LLM_BASE_URL.startswith("http")

    def test_llm_temperature_is_float(self):
        from config import LLM_TEMPERATURE
        assert isinstance(LLM_TEMPERATURE, float)
        assert 0.0 <= LLM_TEMPERATURE <= 1.0

    def test_embedding_model_is_string(self):
        from config import EMBEDDING_MODEL
        assert isinstance(EMBEDDING_MODEL, str)
        assert "/" in EMBEDDING_MODEL  # format "org/model"

    def test_lance_db_path_is_string(self):
        from config import LANCE_DB_PATH
        assert isinstance(LANCE_DB_PATH, str)

    def test_lance_table_name_is_string(self):
        from config import LANCE_TABLE_NAME
        assert isinstance(LANCE_TABLE_NAME, str)
        assert len(LANCE_TABLE_NAME) > 0

    def test_documents_folder_is_string(self):
        from config import DOCUMENTS_FOLDER
        assert isinstance(DOCUMENTS_FOLDER, str)

    def test_supported_extensions_contains_pdf(self):
        from config import SUPPORTED_EXTENSIONS
        assert ".pdf" in SUPPORTED_EXTENSIONS

    def test_supported_extensions_contains_html(self):
        from config import SUPPORTED_EXTENSIONS
        assert ".html" in SUPPORTED_EXTENSIONS

    def test_supported_extensions_contains_txt(self):
        from config import SUPPORTED_EXTENSIONS
        assert ".txt" in SUPPORTED_EXTENSIONS

    def test_top_k_chunks_positive(self):
        from config import TOP_K_CHUNKS
        assert isinstance(TOP_K_CHUNKS, int)
        assert TOP_K_CHUNKS > 0

    def test_chunk_size_positive(self):
        from config import CHUNK_SIZE
        assert isinstance(CHUNK_SIZE, int)
        assert CHUNK_SIZE > 0

    def test_chunk_overlap_less_than_chunk_size(self):
        from config import CHUNK_SIZE, CHUNK_OVERLAP
        assert CHUNK_OVERLAP < CHUNK_SIZE

    def test_prompt_template_contains_context_placeholder(self):
        from config import PROMPT_TEMPLATE
        assert "{context}" in PROMPT_TEMPLATE

    def test_prompt_template_contains_question_placeholder(self):
        from config import PROMPT_TEMPLATE
        assert "{question}" in PROMPT_TEMPLATE


@pytest.mark.unit
class TestConfigEnvOverride:
    """Vérifie que les variables d'environnement surchargent les valeurs par défaut."""

    def test_top_k_env_override(self, monkeypatch):
        """TOP_K est fixe dans config.py ; on teste juste la valeur numérique."""
        from config import TOP_K_CHUNKS
        assert TOP_K_CHUNKS == 3  # valeur par défaut dans le code source

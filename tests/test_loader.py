# =============================================================
# tests/test_loader.py — Tests du module loader.py
# =============================================================

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.documents import Document


@pytest.mark.unit
class TestLoadDocumentsReturnTypes:
    """Vérifie que load_documents retourne toujours une liste."""

    def test_returns_list_when_folder_missing(self, tmp_path):
        """Dossier inexistant → retour liste vide."""
        from loader import load_documents
        result = load_documents(str(tmp_path / "nonexistent"))
        assert isinstance(result, list)
        assert len(result) == 0

    def test_returns_list_when_folder_empty(self, tmp_path):
        """Dossier vide → retour liste vide."""
        from loader import load_documents
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        result = load_documents(str(empty_dir))
        assert isinstance(result, list)
        assert len(result) == 0

    def test_ignores_unsupported_extensions(self, tmp_path):
        """Fichiers .csv et .json ne doivent pas être chargés."""
        (tmp_path / "data.csv").write_text("a,b,c")
        (tmp_path / "config.json").write_text('{"key": "value"}')
        from loader import load_documents
        result = load_documents(str(tmp_path))
        assert result == []


@pytest.mark.unit
class TestLoadDocumentsTxtFiles:
    """Tests sur le chargement de fichiers texte."""

    def test_loads_txt_file(self, tmp_path):
        """Un fichier .txt valide doit produire au moins un Document."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Contenu de test pour pytest.", encoding="utf-8")

        from loader import load_documents
        result = load_documents(str(tmp_path))

        assert len(result) >= 1
        assert all(isinstance(d, Document) for d in result)

    def test_txt_document_has_page_content(self, tmp_path):
        txt_file = tmp_path / "content.txt"
        txt_file.write_text("Données importantes.", encoding="utf-8")

        from loader import load_documents
        result = load_documents(str(tmp_path))

        assert result[0].page_content.strip() != ""

    def test_loads_raw_file_as_txt(self, tmp_path):
        """.raw doit être traité comme du texte brut."""
        raw_file = tmp_path / "dump.raw"
        raw_file.write_text("raw content data", encoding="utf-8")

        from loader import load_documents
        result = load_documents(str(tmp_path))

        assert len(result) >= 1

    def test_loads_multiple_txt_files(self, tmp_path):
        for i in range(3):
            (tmp_path / f"doc{i}.txt").write_text(f"Document {i}", encoding="utf-8")

        from loader import load_documents
        result = load_documents(str(tmp_path))

        assert len(result) >= 3

    def test_source_metadata_present(self, tmp_path):
        """Les métadonnées 'source' doivent être renseignées."""
        (tmp_path / "meta.txt").write_text("Texte avec métadonnées.", encoding="utf-8")

        from loader import load_documents
        result = load_documents(str(tmp_path))

        assert "source" in result[0].metadata


@pytest.mark.unit
class TestLoadDocumentsPDFMocked:
    """Tests PDF avec loader mocké (évite la dépendance à pypdf)."""

    def test_pdf_loader_called(self, tmp_path):
        """PyPDFLoader doit être appelé pour un fichier .pdf."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake content")

        fake_doc = Document(page_content="Contenu PDF simulé.",
                            metadata={"source": str(pdf_file)})

        with patch("loader.PyPDFLoader") as MockPDF:
            instance = MagicMock()
            instance.load.return_value = [fake_doc]
            MockPDF.return_value = instance

            from loader import load_documents
            result = load_documents(str(tmp_path))

        assert len(result) >= 1
        assert result[0].page_content == "Contenu PDF simulé."


@pytest.mark.unit
class TestLoadDocumentsHTMLMocked:
    """Tests HTML avec loader mocké."""

    def test_html_loader_called(self, tmp_path):
        html_file = tmp_path / "page.html"
        html_file.write_text("<html><body>Test</body></html>", encoding="utf-8")

        fake_doc = Document(page_content="Test",
                            metadata={"source": str(html_file)})

        with patch("loader.UnstructuredHTMLLoader") as MockHTML:
            instance = MagicMock()
            instance.load.return_value = [fake_doc]
            MockHTML.return_value = instance

            from loader import load_documents
            result = load_documents(str(tmp_path))

        assert len(result) >= 1


@pytest.mark.unit
class TestLoadDocumentsErrorHandling:
    """Un fichier corrompu ne doit pas faire planter tout le chargement."""

    def test_bad_encoding_skipped(self, tmp_path):
        bad_file = tmp_path / "bad.txt"
        bad_file.write_bytes(b"\xff\xfe bad bytes")

        good_file = tmp_path / "good.txt"
        good_file.write_text("Contenu valide.", encoding="utf-8")

        from loader import load_documents
        result = load_documents(str(tmp_path))
        # Le fichier valide doit toujours être chargé
        assert any("Contenu valide" in d.page_content for d in result)
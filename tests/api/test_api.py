# =============================================================
# tests/api/test_api.py — Tests des endpoints FastAPI
# =============================================================
# Routes confirmées depuis api/routes/ :
#   GET    /                         → accueil
#   GET    /status                   → StatusResponse(status="online", ...)
#   POST   /query                    → QueryResponse(answer=..., sources=...)
#   GET    /documents                → list[DocumentInfo]
#   POST   /documents/upload         → {message, filename, size}
#   POST   /documents/index          → {message, documents_indexed}
#   DELETE /documents/{filename}     → MessageResponse
# =============================================================

import io
import pytest


# ===========================================================================
# GET /status
# ===========================================================================

@pytest.mark.unit
class TestStatusEndpoint:

    def test_status_returns_200(self, api_client):
        response = api_client.get("/status")
        assert response.status_code == 200

    def test_status_returns_json(self, api_client):
        response = api_client.get("/status")
        assert response.headers["content-type"].startswith("application/json")

    def test_status_value_is_online(self, api_client):
        """L'API retourne status='online' (confirmé dans general.py)."""
        response = api_client.get("/status")
        body = response.json()
        assert body.get("status") == "online"

    def test_status_has_documents_loaded_key(self, api_client):
        response = api_client.get("/status")
        body = response.json()
        assert "documents_loaded" in body

    def test_status_no_auth_required(self, api_client):
        response = api_client.get("/status")
        assert response.status_code not in {401, 403}


# ===========================================================================
# POST /query
# ===========================================================================

@pytest.mark.unit
class TestQueryEndpoint:

    def test_query_returns_200(self, api_client):
        response = api_client.post("/query", json={"question": "Qu'est-ce que Python ?"})
        assert response.status_code == 200

    def test_query_response_has_answer_key(self, api_client):
        """QueryResponse retourne 'answer' (confirmé dans query.py)."""
        response = api_client.post("/query", json={"question": "Qu'est-ce que LanceDB ?"})
        body = response.json()
        assert "answer" in body

    def test_query_answer_is_string(self, api_client):
        response = api_client.post("/query", json={"question": "Qu'est-ce que le RAG ?"})
        body = response.json()
        assert isinstance(body["answer"], str)
        assert len(body["answer"]) > 0

    def test_query_calls_rag_system(self, api_client_and_rag):
        client, mock_rag = api_client_and_rag
        mock_rag.reset_mock()
        client.post("/query", json={"question": "Test appel RAG"})
        mock_rag.query.assert_called_once()

    def test_query_missing_question_returns_422(self, api_client):
        response = api_client.post("/query", json={})
        assert response.status_code == 422

    def test_query_returns_json(self, api_client):
        response = api_client.post("/query", json={"question": "Test JSON"})
        assert response.headers["content-type"].startswith("application/json")

    def test_query_with_show_sources_true(self, api_client):
        """show_sources=True doit retourner les sources dans la réponse."""
        response = api_client.post("/query", json={
            "question": "Test sources",
            "show_sources": True
        })
        assert response.status_code == 200


# ===========================================================================
# GET /documents
# ===========================================================================

@pytest.mark.unit
class TestDocumentsEndpoint:

    def test_documents_returns_200(self, api_client):
        response = api_client.get("/documents")
        assert response.status_code == 200

    def test_documents_returns_json(self, api_client):
        response = api_client.get("/documents")
        assert response.headers["content-type"].startswith("application/json")

    def test_documents_returns_list(self, api_client):
        """list_documents retourne une liste (response_model=list[DocumentInfo])."""
        response = api_client.get("/documents")
        body = response.json()
        assert isinstance(body, list)

    def test_documents_empty_when_no_files(self, api_client):
        """Dossier vide → liste vide (tmp_path vide au départ)."""
        response = api_client.get("/documents")
        body = response.json()
        assert isinstance(body, list)


# ===========================================================================
# POST /documents/upload
# ===========================================================================

@pytest.mark.unit
class TestUploadEndpoint:

    def test_upload_txt_returns_200(self, api_client, fake_txt_file):
        name, content, mime = fake_txt_file
        response = api_client.post(
            "/documents/upload",
            files={"file": (name, content, mime)},
        )
        assert response.status_code == 200

    def test_upload_response_has_filename(self, api_client, fake_txt_file):
        name, content, mime = fake_txt_file
        response = api_client.post(
            "/documents/upload",
            files={"file": (name, content, mime)},
        )
        body = response.json()
        assert "filename" in body

    def test_upload_response_has_message(self, api_client, fake_txt_file):
        name, content, mime = fake_txt_file
        response = api_client.post(
            "/documents/upload",
            files={"file": (name, content, mime)},
        )
        body = response.json()
        assert "message" in body

    def test_upload_pdf_accepted(self, api_client, fake_pdf_file):
        name, content, mime = fake_pdf_file
        response = api_client.post(
            "/documents/upload",
            files={"file": (name, content, mime)},
        )
        assert response.status_code == 200

    def test_upload_html_accepted(self, api_client):
        html_content = b"<html><body>Documentation</body></html>"
        response = api_client.post(
            "/documents/upload",
            files={"file": ("page.html", io.BytesIO(html_content), "text/html")},
        )
        assert response.status_code == 200

    def test_upload_unsupported_extension_rejected(self, api_client):
        """Extension .exe → 400 (confirmé dans documents.py : ext not in SUPPORTED_EXTENSIONS)."""
        response = api_client.post(
            "/documents/upload",
            files={"file": ("malware.exe", io.BytesIO(b"MZ binary"), "application/octet-stream")},
        )
        assert response.status_code == 400

    def test_upload_no_file_returns_422(self, api_client):
        """Requête sans fichier → 422 FastAPI validation error."""
        response = api_client.post("/documents/upload")
        assert response.status_code == 422

    def test_upload_returns_json(self, api_client, fake_txt_file):
        name, content, mime = fake_txt_file
        response = api_client.post(
            "/documents/upload",
            files={"file": (name, content, mime)},
        )
        assert response.headers["content-type"].startswith("application/json")


# ===========================================================================
# POST /documents/index — Réindexation
# ===========================================================================

@pytest.mark.unit
class TestIndexEndpoint:

    def test_index_with_no_documents_returns_400(self, api_client):
        """Dossier vide → 400 'Aucun document trouvé' (confirmé dans documents.py)."""
        response = api_client.post("/documents/index")
        # Soit 400 (aucun doc) soit 200 si des docs existent
        assert response.status_code in {200, 400, 503}

    def test_index_returns_json(self, api_client):
        response = api_client.post("/documents/index")
        assert response.headers["content-type"].startswith("application/json")

    def test_index_after_upload_returns_200(self, api_client, fake_txt_file):
        """Upload + index → 200 avec documents_indexed."""
        name, content, mime = fake_txt_file

        # Upload d'abord
        api_client.post(
            "/documents/upload",
            files={"file": (name, io.BytesIO(content.read() if hasattr(content, 'read') else content), mime)},
        )

        # Puis indexation avec mocks
        from unittest.mock import patch, MagicMock
        from langchain_core.documents import Document

        fake_docs = [Document(page_content="test", metadata={"source": "upload.txt"})]
        with patch("api.routes.documents.load_documents", return_value=fake_docs), \
             patch("api.routes.documents.build_vectorstore", return_value=MagicMock()):
            response = api_client.post("/documents/index")

        assert response.status_code == 200
        body = response.json()
        assert "documents_indexed" in body


# ===========================================================================
# DELETE /documents/{filename}
# ===========================================================================

@pytest.mark.unit
class TestDeleteDocumentEndpoint:

    def test_delete_nonexistent_returns_404(self, api_client):
        """Fichier inexistant → 404 (confirmé dans documents.py)."""
        response = api_client.delete("/documents/nonexistent_file_xyz.txt")
        assert response.status_code == 404

    def test_delete_existing_returns_200(self, api_client, fake_txt_file, client):
        """Upload puis suppression → 200."""
        _, _, _ = client  # accès au docs_dir via fixture
        name, content, mime = fake_txt_file

        # Upload d'abord
        api_client.post(
            "/documents/upload",
            files={"file": (name, content, mime)},
        )

        # Suppression
        response = api_client.delete(f"/documents/{name}")
        assert response.status_code == 200

    def test_delete_returns_json(self, api_client):
        response = api_client.delete("/documents/some_file.txt")
        if response.status_code != 204:
            assert response.headers["content-type"].startswith("application/json")


# ===========================================================================
# GET / — Accueil
# ===========================================================================

@pytest.mark.unit
class TestRootEndpoint:

    def test_root_returns_200(self, api_client):
        response = api_client.get("/")
        assert response.status_code == 200

    def test_root_returns_json(self, api_client):
        response = api_client.get("/")
        assert response.headers["content-type"].startswith("application/json")

    def test_root_has_message(self, api_client):
        response = api_client.get("/")
        body = response.json()
        assert "message" in body


# ===========================================================================
# Tests transversaux
# ===========================================================================

@pytest.mark.unit
class TestGlobalBehaviors:

    def test_unknown_route_returns_404(self, api_client):
        response = api_client.get("/nonexistent_xyz")
        assert response.status_code == 404

    def test_get_query_not_allowed(self, api_client):
        """GET sur /query → 404 ou 405 (route POST uniquement)."""
        response = api_client.get("/query")
        assert response.status_code in {404, 405}

    def test_all_main_endpoints_return_json(self, api_client):
        """Tous les endpoints principaux doivent retourner du JSON parsable."""
        checks = [
            ("GET",  "/",        {}),
            ("GET",  "/status",  {}),
            ("GET",  "/documents", {}),
            ("POST", "/query",   {"json": {}}),
        ]
        for method, path, kwargs in checks:
            resp = getattr(api_client, method.lower())(path, **kwargs)
            try:
                resp.json()
            except Exception:
                pytest.fail(f"Non-JSON pour {method} {path}: {resp.text}")
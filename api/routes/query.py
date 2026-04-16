# =============================================================
# api/routes/query.py — Endpoint /query
# =============================================================

from fastapi import APIRouter, HTTPException

from api.models import QueryRequest, QueryResponse, SourceDocument
from api.dependencies import get_rag

router = APIRouter(prefix="/query", tags=["RAG"])


@router.post("", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """
    Pose une question au système RAG.

    - **question**: La question en langage naturel
    - **show_sources**: Inclure les documents sources dans la réponse
    """
    rag = get_rag()

    if rag is None or rag.vectorstore is None:
        raise HTTPException(
            status_code=503,
            detail="Le système RAG n'est pas encore initialisé. Indexez des documents d'abord via POST /documents/index.",
        )

    try:
        result = rag.query(request.question, show_sources=False)

        sources = None
        if request.show_sources and "source_documents" in result:
            sources = [
                SourceDocument(
                    source=doc.metadata.get("source", "Inconnu"),
                    content=doc.page_content[:300],
                )
                for doc in result["source_documents"]
            ]

        return QueryResponse(answer=result["result"], sources=sources)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

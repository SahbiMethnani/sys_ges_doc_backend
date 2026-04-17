FROM python:3.12-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-docker.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY config.py embeddings.py llm.py loader.py vectorstore.py rag.py main.py rag_system.py /app/
COPY api /app/api/
COPY documents /app/documents/

ENV PYTHONUNBUFFERED=1 \
    DOCUMENTS_FOLDER=/app/documents \
    LANCE_DB_PATH=/app/lance_db

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -sf http://127.0.0.1:8000/status || exit 1

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

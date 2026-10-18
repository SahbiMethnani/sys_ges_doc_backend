FROM python:3.11-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-docker.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --default-timeout=300 --retries=10 -r /tmp/requirements.txt

COPY . /app/

# Échec du build si le module auth LDAP n'est pas présent dans l'image
RUN test -f /app/api/auth/router.py && test -f /app/api/db/models.py

ENV PYTHONUNBUFFERED=1 \
    DOCUMENTS_FOLDER=/app/documents \
    LANCE_DB_PATH=/app/lance_db

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -sf http://127.0.0.1:8000/status || exit 1

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

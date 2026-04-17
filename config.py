# =============================================================
# config.py — Configuration centralisée du système RAG
# =============================================================

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CUDA_VISIBLE_DEVICES"] = ""

# --- LLM ---
LLM_MODEL = os.environ.get("LLM_MODEL", "mistral")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "http://localhost:11434")
LLM_TEMPERATURE = float(os.environ.get("LLM_TEMPERATURE", "0.1"))

# --- Embeddings ---
EMBEDDING_MODEL = os.environ.get(
    "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)
EMBEDDING_DEVICE = os.environ.get("EMBEDDING_DEVICE", "cpu")

# --- LanceDB (stockage local, meilleure tenue sous Windows que ChromaDB) ---
LANCE_DB_PATH = os.environ.get("LANCE_DB_PATH", "./lance_db")
LANCE_TABLE_NAME = os.environ.get("LANCE_TABLE_NAME", "documents")

# --- Documents ---
DOCUMENTS_FOLDER = os.environ.get("DOCUMENTS_FOLDER", "./documents")
SUPPORTED_EXTENSIONS = {".pdf", ".html", ".txt", ".raw"}

# --- Retrieval ---
TOP_K_CHUNKS = 3        # Nombre de chunks à récupérer
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# --- Prompt ---
PROMPT_TEMPLATE = """Tu es un assistant documentaire. Réponds en français uniquement.
Utilise UNIQUEMENT les informations du contexte ci-dessous pour répondre.
Donne UNE SEULE réponse courte et directe à la question posée.
Si l'information n'est pas dans le contexte, réponds : "Information non disponible dans la documentation."

Contexte:
{context}

Question: {question}

Réponse (courte et directe):"""
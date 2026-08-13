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


#ChromaDBPATH = os.environ.get("CHROMADB_PATH", "./chroma_db")

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

# --- MySQL ---
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "mysql+pymysql://root:root@localhost:3306/sys_ges_doc",
)

# --- JWT ---
JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_EXPIRE_MINUTES = int(os.environ.get("JWT_ACCESS_EXPIRE_MINUTES", "60"))
JWT_REFRESH_EXPIRE_DAYS = int(os.environ.get("JWT_REFRESH_EXPIRE_DAYS", "7"))

# --- LDAP ---
LDAP_SERVER = os.environ.get("LDAP_SERVER", "ldap://localhost")
LDAP_PORT = int(os.environ.get("LDAP_PORT", "389"))
LDAP_USE_SSL = os.environ.get("LDAP_USE_SSL", "false").lower() in ("1", "true", "yes")
LDAP_BASE_DN = os.environ.get("LDAP_BASE_DN", "dc=sysgesdoc,dc=local")
LDAP_BIND_DN = os.environ.get("LDAP_BIND_DN", "cn=admin,dc=sysgesdoc,dc=local")
LDAP_BIND_PASSWORD = os.environ.get("LDAP_BIND_PASSWORD", "admin")
LDAP_USER_SEARCH_BASE = os.environ.get(
    "LDAP_USER_SEARCH_BASE", "ou=users,dc=sysgesdoc,dc=local"
)
LDAP_USER_SEARCH_FILTER = os.environ.get(
    "LDAP_USER_SEARCH_FILTER", "(uid={username})"
)
LDAP_ORGANISATION = os.environ.get("LDAP_ORGANISATION", "SysGesDoc")

# --- Auth / seed ---
AUTH_DISABLED = os.environ.get("AUTH_DISABLED", "false").lower() in ("1", "true", "yes")
SEED_ADMIN_USERNAME = os.environ.get("SEED_ADMIN_USERNAME", "Sahbi")
SEED_ADMIN_DISPLAY_NAME = os.environ.get("SEED_ADMIN_DISPLAY_NAME", "Sahbi Admin")
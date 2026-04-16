# =============================================================
# config.py — Configuration centralisée du système RAG
# =============================================================

# Désactiver la télémétrie ChromaDB (doit être fait avant tout import chromadb)
import os
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY"] = "False"
os.environ["CUDA_VISIBLE_DEVICES"] = ""

# --- LLM ---
LLM_MODEL = "mistral"            # Modèle Ollama: tinyllama, mistral, llama3...
LLM_BASE_URL = "http://localhost:11434"
LLM_TEMPERATURE = 0.1            # Bas = réponses plus précises et courtes

# --- Embeddings ---
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
# Pour le français: "dangvantuan/sentence-camembert-large"
EMBEDDING_DEVICE = "cpu"

# --- ChromaDB ---
CHROMA_PERSIST_DIR = "./chroma_db"

# --- Documents ---
DOCUMENTS_FOLDER = "./documents"
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
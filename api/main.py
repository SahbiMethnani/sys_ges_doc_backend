# =============================================================
# api/main.py — Point d'entrée FastAPI
# =============================================================

import os
import sys
import warnings

os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CUDA_VISIBLE_DEVICES"] = ""
warnings.filterwarnings("ignore")

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ajouter le dossier racine au path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DOCUMENTS_FOLDER
from vectorstore import vector_index_exists
from embeddings import get_embeddings
from llm import get_llm
from rag import RAGSystem
from vectorstore import load_vectorstore

from api.dependencies import set_rag
from api.routes import general, query, documents
from api.auth.router import router as auth_router
from api.auth.user_service import ensure_admin_seed
from api.db.session import SessionLocal

# ------------------------------------------------------------------
# Application FastAPI
# ------------------------------------------------------------------

app = FastAPI(
    title="RAG API",
    description="API REST pour interroger des documents via RAG (LangChain + LanceDB + Ollama)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — Angular dev, Docker frontend, Kubernetes ingress
_cors_env = os.environ.get(
    "CORS_ORIGINS",
    "http://localhost:4200,http://localhost:4000,http://127.0.0.1:4200",
)
CORS_ORIGINS = [o.strip() for o in _cors_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------
# Enregistrement des routes
# ------------------------------------------------------------------

app.include_router(auth_router)
app.include_router(general.router)
app.include_router(query.router)
app.include_router(documents.router)

# ------------------------------------------------------------------
# Démarrage
# ------------------------------------------------------------------

@app.on_event("startup")
async def startup_event():
    """Initialise le système RAG au démarrage du serveur."""
    print("🚀 Démarrage de l'API RAG...")

    try:
        db = SessionLocal()
        ensure_admin_seed(db)
        db.close()
        print("✅ Utilisateur admin MySQL vérifié (Sahbi)")
    except Exception as e:
        print(f"⚠️  MySQL non disponible — auth limitée : {e}")

    os.makedirs(DOCUMENTS_FOLDER, exist_ok=True)

    embeddings = get_embeddings()
    llm = get_llm()
    rag = RAGSystem(vectorstore=None, llm=llm)
    rag.embeddings = embeddings  # Exposé pour la réindexation

    if vector_index_exists():
        try:
            rag.vectorstore = load_vectorstore(embeddings)
            print("✅ Base vectorielle chargée automatiquement")
        except Exception as e:
            print(f"⚠️  Impossible de charger la base vectorielle : {e}")
    else:
        print("⚠️  Aucune base vectorielle trouvée. Uploadez des documents puis appelez POST /documents/index")

    set_rag(rag)
    print("✅ Système RAG prêt")


# ------------------------------------------------------------------
# Lancement direct
# ------------------------------------------------------------------

if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════════════╗
    ║        API RAG  —  Serveur en cours...         ║
    ╚════════════════════════════════════════════════╝

    📡 URL       : http://localhost:8000
    📚 Swagger   : http://localhost:8000/docs
    🔄 ReDoc     : http://localhost:8000/redoc

    Endpoints :
      POST  /auth/login            → Connexion LDAP
      POST  /auth/register         → Inscription
      GET   /auth/me               → Profil (Bearer token)
      POST  /query                 → Poser une question (authentifié)
      GET   /documents             → Lister les documents (admin)
      POST  /documents/upload      → Uploader un document
      POST  /documents/index       → Réindexer les documents
      DELETE /documents/{filename} → Supprimer un document
      GET   /status                → Statut du système

    CTRL+C pour arrêter
    """)

    uvicorn.run("api.main:app", host="0.0.0.0", port=8000)

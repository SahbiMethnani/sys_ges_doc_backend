# =============================================================
# api/dependencies.py — Instance partagée du système RAG
# =============================================================

import sys
import os

# Ajouter le dossier parent au path pour importer les modules RAG
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag import RAGSystem

# Instance globale partagée entre tous les endpoints
rag_system: RAGSystem | None = None


def get_rag() -> RAGSystem | None:
    """Retourne l'instance RAG globale."""
    return rag_system


def set_rag(instance: RAGSystem):
    """Définit l'instance RAG globale."""
    global rag_system
    rag_system = instance

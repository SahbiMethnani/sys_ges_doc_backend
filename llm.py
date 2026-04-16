# =============================================================
# llm.py — Initialisation du modèle LLM via Ollama
# =============================================================

from langchain_community.llms import Ollama
from config import LLM_MODEL, LLM_BASE_URL, LLM_TEMPERATURE


def get_llm(model_name: str = LLM_MODEL) -> Ollama:
    """
    Crée et retourne une instance du LLM Ollama.

    Args:
        model_name: Nom du modèle Ollama (ex: tinyllama, mistral, llama3).

    Returns:
        Instance Ollama configurée.
    """
    print(f"🤖 Initialisation du modèle LLM ({model_name})...")
    return Ollama(
        model=model_name,
        base_url=LLM_BASE_URL,
        temperature=LLM_TEMPERATURE,
    )
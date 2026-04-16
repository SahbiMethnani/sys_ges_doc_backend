
from langchain_community.embeddings import HuggingFaceEmbeddings
from config import EMBEDDING_MODEL, EMBEDDING_DEVICE


def get_embeddings() -> HuggingFaceEmbeddings:
    """
    Charge et retourne le modèle d'embeddings HuggingFace.

    Returns:
        Instance HuggingFaceEmbeddings prête à l'emploi.
    """
    print(f"📦 Chargement des embeddings ({EMBEDDING_MODEL})...")
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": EMBEDDING_DEVICE},
    )
    
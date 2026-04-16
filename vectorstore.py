# =============================================================
# vectorstore.py — Gestion de la base vectorielle ChromaDB
# =============================================================

from typing import List

from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter

from config import CHROMA_PERSIST_DIR, CHUNK_SIZE, CHUNK_OVERLAP


def build_vectorstore(documents: List, embeddings) -> Chroma:
    """
    Découpe les documents en chunks et crée la base ChromaDB.

    Args:
        documents: Documents LangChain chargés.
        embeddings: Modèle d'embeddings.

    Returns:
        Instance Chroma indexée et persistée sur disque.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", " ", ""],
    )

    print("✂️  Découpage des documents en chunks...")
    chunks = splitter.split_documents(documents)
    print(f"📊 {len(chunks)} chunk(s) créé(s)")

    print("🔍 Indexation dans ChromaDB...")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PERSIST_DIR,
    )
    print(f"💾 Base sauvegardée dans {CHROMA_PERSIST_DIR}")
    return vectorstore


def load_vectorstore(embeddings) -> Chroma:
    """
    Charge une base ChromaDB existante depuis le disque.

    Args:
        embeddings: Modèle d'embeddings (doit être identique à celui utilisé à la création).

    Returns:
        Instance Chroma chargée.
    """
    print(f"📖 Chargement de la base vectorielle depuis {CHROMA_PERSIST_DIR}...")
    vectorstore = Chroma(
        persist_directory=CHROMA_PERSIST_DIR,
        embedding_function=embeddings,
    )
    print("✅ Base vectorielle chargée")
    return vectorstore
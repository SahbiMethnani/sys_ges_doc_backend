# =============================================================
# vectorstore.py — Gestion de la base vectorielle LanceDB
# =============================================================

import os
from typing import List

import lancedb
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import LanceDB

from config import CHUNK_OVERLAP, CHUNK_SIZE, LANCE_DB_PATH, LANCE_TABLE_NAME


def vector_index_exists() -> bool:
    """True si le dossier LanceDB existe et contient la table d'index."""
    if not os.path.isdir(LANCE_DB_PATH):
        return False
    try:
        conn = lancedb.connect(LANCE_DB_PATH)
        return LANCE_TABLE_NAME in conn.table_names()
    except OSError:
        return False


def build_vectorstore(documents: List, embeddings) -> LanceDB:
    """
    Découpe les documents en chunks et crée la base LanceDB.

    Args:
        documents: Documents LangChain chargés.
        embeddings: Modèle d'embeddings.

    Returns:
        Instance LanceDB indexée et persistée sur disque.
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

    print("🔍 Indexation dans LanceDB...")
    conn = lancedb.connect(LANCE_DB_PATH)
    vectorstore = LanceDB.from_documents(
        documents=chunks,
        embedding=embeddings,
        connection=conn,
        table_name=LANCE_TABLE_NAME,
        mode="overwrite",
    )
    print(f"💾 Base sauvegardée dans {LANCE_DB_PATH} (table {LANCE_TABLE_NAME})")
    return vectorstore


def load_vectorstore(embeddings) -> LanceDB:
    """
    Charge une base LanceDB existante depuis le disque.

    Args:
        embeddings: Modèle d'embeddings (doit être identique à celui utilisé à la création).

    Returns:
        Instance LanceDB chargée.
    """
    print(f"📖 Chargement de la base vectorielle depuis {LANCE_DB_PATH}...")
    conn = lancedb.connect(LANCE_DB_PATH)
    if LANCE_TABLE_NAME not in conn.table_names():
        raise FileNotFoundError(
            f"Table LanceDB « {LANCE_TABLE_NAME} » absente. Réindexez les documents."
        )
    vectorstore = LanceDB(
        connection=conn,
        embedding=embeddings,
        table_name=LANCE_TABLE_NAME,
    )
    print("✅ Base vectorielle chargée")
    return vectorstore

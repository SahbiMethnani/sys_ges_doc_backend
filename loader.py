
from pathlib import Path
from typing import List

from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredHTMLLoader,
    TextLoader,
)

from config import DOCUMENTS_FOLDER, SUPPORTED_EXTENSIONS


def load_documents(documents_path: str = DOCUMENTS_FOLDER) -> List:
    """
    Parcourt récursivement un dossier et charge tous les fichiers supportés.

    Args:
        documents_path: Chemin du dossier contenant les documents.

    Returns:
        Liste de documents LangChain.
    """
    documents = []
    path = Path(documents_path)

    if not path.exists():
        print(f"⚠️  Dossier introuvable: {documents_path}")
        return documents

    print(f"📂 Chargement des documents depuis {documents_path}...")

    for file_path in path.rglob("*"):
        if not file_path.is_file():
            continue

        ext = file_path.suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            continue

        try:
            if ext == ".pdf":
                print(f"  📄 PDF     : {file_path.name}")
                loader = PyPDFLoader(str(file_path))

            elif ext == ".html":
                print(f"  🌐 HTML    : {file_path.name}")
                import nltk
                nltk.download('averaged_perceptron_tagger_eng', quiet=True)
                nltk.download('punkt_tab', quiet=True)
                loader = UnstructuredHTMLLoader(str(file_path))
                

            elif ext in {".txt", ".raw"}:
                print(f"  📝 Texte   : {file_path.name}")
                loader = TextLoader(str(file_path), encoding="utf-8")

            else:
                continue

            documents.extend(loader.load())

        except Exception as e:
            print(f"  ⚠️  Erreur [{file_path.name}]: {e}")

    print(f"✅ {len(documents)} document(s) chargé(s)")
    return documents
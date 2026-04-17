import os
import warnings

os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CUDA_VISIBLE_DEVICES"] = ""
warnings.filterwarnings("ignore") 

import shutil

from config import DOCUMENTS_FOLDER, LANCE_DB_PATH
from embeddings import get_embeddings
from llm import get_llm
from loader import load_documents
from vectorstore import build_vectorstore, load_vectorstore, vector_index_exists
from rag import RAGSystem


def setup_vectorstore(embeddings):
    """
    Gère le chargement ou la création de la base vectorielle.

    Returns:
        Instance LanceDB prête à l'emploi.
    """
    print("=" * 60)
    print("🚀 SYSTÈME RAG — CHARGEMENT DES DOCUMENTS")
    print("=" * 60)

    # Créer le dossier documents s'il n'existe pas
    if not os.path.exists(DOCUMENTS_FOLDER):
        os.makedirs(DOCUMENTS_FOLDER)
        print(f"\n⚠️  Dossier '{DOCUMENTS_FOLDER}' créé.")
        print("   Ajoutez vos fichiers (.pdf, .html, .txt, .raw) puis relancez.")
        return None

    # Base existante → proposer de la réutiliser
    if vector_index_exists():
        print("\n📚 Base vectorielle existante détectée.")
        choice = input("(1) Recharger les documents  (2) Utiliser la base existante [1/2]: ").strip()

        if choice == "1":
            shutil.rmtree(LANCE_DB_PATH, ignore_errors=True)
            documents = load_documents(DOCUMENTS_FOLDER)
            if not documents:
                print("⚠️  Aucun document trouvé.")
                return None
            return build_vectorstore(documents, embeddings)

        else:
            return load_vectorstore(embeddings)

    # Première utilisation
    documents = load_documents(DOCUMENTS_FOLDER)
    if not documents:
        print("⚠️  Aucun document trouvé. Ajoutez des fichiers dans 'documents/'")
        return None

    return build_vectorstore(documents, embeddings)


def interactive_loop(rag: RAGSystem):
    """Boucle interactive de questions-réponses."""
    print("\n" + "=" * 60)
    print("💬 MODE QUESTION-RÉPONSE")
    print("=" * 60)
    print("Tapez 'quit' pour quitter\n")

    while True:
        question = input("🔎 Votre question: ").strip()

        if question.lower() in {"quit", "exit", "q"}:
            print("\n👋 Au revoir!")
            break

        if not question:
            continue

        try:
            rag.query(question, show_sources=True)
        except Exception as e:
            print(f"\n❌ Erreur: {e}")

        print("\n" + "-" * 60)


def main():
    # 1. Initialiser les composants
    embeddings = get_embeddings()
    llm = get_llm()

    # 2. Préparer la base vectorielle
    vectorstore = setup_vectorstore(embeddings)
    if vectorstore is None:
        return

    rag = RAGSystem(vectorstore=vectorstore, llm=llm)

    # 4. Lancer l'interface interactive
    interactive_loop(rag)


if __name__ == "__main__":
    main()
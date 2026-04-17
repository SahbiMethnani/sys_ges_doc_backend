"""
Système RAG complet pour PFE
Documents supportés: PDF, HTML, .raw (texte brut)
Base vectorielle: LanceDB
LLM: Modèles open-source (Llama/Mistral via Ollama)
"""

import os
import shutil
from pathlib import Path
from typing import List

import lancedb
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredHTMLLoader,
)
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import LanceDB
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_community.llms import Ollama

from rag import chunk_document_source


class RAGSystem:
    """Système RAG pour documentation technique"""
    
    def __init__(
        self,
        persist_directory: str = "./lance_db",
        table_name: str = "documents",
        model_name: str = "mistral",
    ):
        """
        Initialiser le système RAG

        Args:
            persist_directory: Dossier LanceDB (URI locale)
            table_name: Nom de la table vectorielle
            model_name: Modèle Ollama à utiliser (mistral, llama2, etc.)
        """
        self.persist_directory = persist_directory
        self.table_name = table_name
        self.model_name = model_name
        
        # Embeddings - modèle français si besoin
        print("📦 Chargement du modèle d'embeddings...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            # Pour le français: "dangvantuan/sentence-camembert-large"
            model_kwargs={'device': 'cpu'}
        )
        
        # Initialiser le vector store
        self.vectorstore = None
        
        # LLM Ollama
        print(f"🤖 Initialisation du modèle {model_name}...")
        self.llm = Ollama(
            model=model_name,
            temperature=0.7
        )
        
        # Text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def load_documents(self, documents_path: str) -> List:
        """
        Charger tous les documents d'un dossier
        
        Args:
            documents_path: Chemin vers le dossier contenant les documents
        
        Returns:
            Liste des documents chargés
        """
        documents = []
        path = Path(documents_path)
        
        print(f"📂 Chargement des documents depuis {documents_path}...")
        
        for file_path in path.rglob("*"):
            if not file_path.is_file():
                continue
                
            file_ext = file_path.suffix.lower()
            
            try:
                # Charger selon le type de fichier
                if file_ext == ".pdf":
                    print(f"  📄 Chargement PDF: {file_path.name}")
                    loader = PyPDFLoader(str(file_path))
                    documents.extend(loader.load())
                    
                elif file_ext == ".html":
                    print(f"  🌐 Chargement HTML: {file_path.name}")
                    loader = UnstructuredHTMLLoader(str(file_path))
                    documents.extend(loader.load())
                    
                elif file_ext == ".raw" or file_ext == ".txt":
                    print(f"  📝 Chargement texte brut: {file_path.name}")
                    loader = TextLoader(str(file_path), encoding='utf-8')
                    documents.extend(loader.load())
                    
            except Exception as e:
                print(f"  ⚠️  Erreur lors du chargement de {file_path.name}: {e}")
        
        print(f"✅ {len(documents)} documents chargés avec succès")
        return documents
    
    def process_documents(self, documents: List):
        """
        Découper et indexer les documents dans LanceDB
        
        Args:
            documents: Liste des documents à traiter
        """
        print("\n✂️  Découpage des documents en chunks...")
        chunks = self.text_splitter.split_documents(documents)
        print(f"📊 {len(chunks)} chunks créés")
        
        print("\n🔍 Création des embeddings et indexation dans LanceDB...")
        conn = lancedb.connect(self.persist_directory)
        self.vectorstore = LanceDB.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            connection=conn,
            table_name=self.table_name,
            mode="overwrite",
        )
        
        print(f"💾 Base vectorielle sauvegardée dans {self.persist_directory}")
    
    def load_existing_vectorstore(self):
        """Charger une base vectorielle existante"""
        print(f"📖 Chargement de la base vectorielle depuis {self.persist_directory}...")
        conn = lancedb.connect(self.persist_directory)
        if self.table_name not in conn.table_names():
            raise FileNotFoundError(
                f"Table LanceDB « {self.table_name} » absente. Indexez d'abord les documents."
            )
        self.vectorstore = LanceDB(
            connection=conn,
            embedding=self.embeddings,
            table_name=self.table_name,
        )
        print("✅ Base vectorielle chargée")
    
    def create_qa_chain(self):
        """Créer la chaîne de question-réponse"""
        if self.vectorstore is None:
            raise ValueError("Aucune base vectorielle chargée. Utilisez load_documents() ou load_existing_vectorstore()")
        
        # Template de prompt personnalisé
        template = """Utilise le contexte suivant pour répondre à la question de manière précise et détaillée.
Si tu ne connais pas la réponse, dis simplement que tu ne sais pas, n'invente pas de réponse.

Contexte: {context}

Question: {question}

Réponse détaillée:"""
        
        prompt = PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
        
        # Créer la chaîne QA
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(
                search_kwargs={"k": 3}  # Top 3 chunks les plus pertinents
            ),
            return_source_documents=True,
            chain_type_kwargs={"prompt": prompt}
        )
        
        return qa_chain
    
    def query(self, question: str, show_sources: bool = True):
        """
        Poser une question au système RAG
        
        Args:
            question: La question à poser
            show_sources: Afficher les sources utilisées
        
        Returns:
            Réponse du système
        """
        qa_chain = self.create_qa_chain()
        
        print(f"\n❓ Question: {question}")
        print("🤔 Recherche dans la documentation...")
        
        result = qa_chain({"query": question})
        
        print(f"\n💡 Réponse:\n{result['result']}")
        
        if show_sources and 'source_documents' in result:
            print("\n📚 Sources utilisées:")
            for i, doc in enumerate(result['source_documents'], 1):
                print(f"  {i}. {chunk_document_source(doc)}")
                print(f"     Extrait: {doc.page_content[:200]}...")
        
        return result


def main():
    """Exemple d'utilisation"""
    
    # Initialiser le système RAG
    rag = RAGSystem(
        persist_directory="./lance_db",
        model_name="mistral",  # ou "llama2", "llama3", etc.
    )
    
    # Option 1: Charger de nouveaux documents
    print("="*60)
    print("🚀 SYSTÈME RAG - CHARGEMENT DES DOCUMENTS")
    print("="*60)
    
    # Créer un dossier exemple si nécessaire
    documents_folder = "./documents"
    if not os.path.exists(documents_folder):
        os.makedirs(documents_folder)
        print(f"\n⚠️  Créez le dossier '{documents_folder}' et ajoutez vos documents (.pdf, .html, .raw)")
        print("   Puis relancez le script.")
        return
    
    # Vérifier si la base existe déjà
    conn = lancedb.connect(rag.persist_directory)
    if rag.table_name in conn.table_names():
        print("\n📚 Base vectorielle existante détectée.")
        choice = input(
            "Voulez-vous (1) Recharger les documents ou (2) Utiliser la base existante? [1/2]: "
        )

        if choice == "1":
            shutil.rmtree(rag.persist_directory, ignore_errors=True)
            documents = rag.load_documents(documents_folder)
            rag.process_documents(documents)
        else:
            rag.load_existing_vectorstore()
    else:
        documents = rag.load_documents(documents_folder)
        if not documents:
            print("\n⚠️  Aucun document trouvé. Ajoutez des fichiers dans le dossier 'documents'")
            return
        rag.process_documents(documents)
    
    # Interface de questions-réponses
    print("\n" + "="*60)
    print("💬 MODE QUESTION-RÉPONSE")
    print("="*60)
    print("Tapez 'quit' pour quitter\n")
    
    while True:
        question = input("🔎 Votre question: ").strip()
        
        if question.lower() in ['quit', 'exit', 'q']:
            print("\n👋 Au revoir!")
            break
        
        if not question:
            continue
        
        try:
            rag.query(question, show_sources=True)
        except Exception as e:
            print(f"\n❌ Erreur: {e}")
        
        print("\n" + "-"*60)


if __name__ == "__main__":
    main()
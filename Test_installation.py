"""
Script de test pour vérifier l'installation du système RAG
"""

import sys

def check_imports():
    """Vérifier que tous les packages sont installés"""
    print("🔍 Vérification des packages...\n")
    
    packages = [
        ("langchain", "LangChain"),
        ("chromadb", "ChromaDB"),
        ("sentence_transformers", "Sentence Transformers"),
        ("pypdf", "PyPDF"),
        ("ollama", "Ollama"),
    ]
    
    missing = []
    
    for package, name in packages:
        try:
            __import__(package)
            print(f"✅ {name} : OK")
        except ImportError:
            print(f"❌ {name} : MANQUANT")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Packages manquants: {', '.join(missing)}")
        print("Installez-les avec: pip install -r requirements.txt")
        return False
    else:
        print("\n✅ Tous les packages sont installés!")
        return True


def check_ollama():
    """Vérifier qu'Ollama est en cours d'exécution"""
    print("\n🔍 Vérification d'Ollama...\n")
    
    try:
        import ollama
        
        # Tenter de lister les modèles
        models = ollama.list()
        
        print("✅ Ollama est en cours d'exécution")
        
        if models.get('models'):
            print("\n📦 Modèles disponibles:")
            for model in models['models']:
                print(f"  - {model['name']}")
        else:
            print("\n⚠️  Aucun modèle installé")
            print("Installez un modèle avec: ollama pull mistral")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        print("\n💡 Solutions:")
        print("  1. Installez Ollama: https://ollama.ai/download")
        print("  2. Lancez Ollama: ollama serve")
        print("  3. Téléchargez un modèle: ollama pull mistral")
        return False


def check_embeddings():
    """Tester le chargement du modèle d'embeddings"""
    print("\n🔍 Test du modèle d'embeddings...\n")
    
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        
        print("Chargement du modèle (peut prendre quelques secondes)...")
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        
        # Tester avec un texte simple
        test_text = "Ceci est un test"
        vector = embeddings.embed_query(test_text)
        
        print(f"✅ Modèle chargé avec succès!")
        print(f"   Dimension des vecteurs: {len(vector)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def test_simple_rag():
    """Test complet du système RAG avec un document simple"""
    print("\n🔍 Test du système RAG complet...\n")
    
    try:
        import os
        import tempfile
        from pathlib import Path
        
        from langchain_community.document_loaders import TextLoader
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from langchain_community.embeddings import HuggingFaceEmbeddings
        from langchain_community.vectorstores import Chroma
        from langchain_community.llms import Ollama
        from langchain.chains import RetrievalQA
        
        # Créer un document de test temporaire
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as f:
            f.write("""
            Documentation de test pour le système RAG.
            
            L'application se déploie avec Docker. La commande principale est: docker-compose up -d
            
            Pour arrêter l'application, utilisez: docker-compose down
            
            Les logs sont disponibles avec: docker-compose logs -f
            """)
            temp_file = f.name
        
        print("1️⃣ Chargement du document test...")
        loader = TextLoader(temp_file, encoding='utf-8')
        documents = loader.load()
        print(f"   ✅ Document chargé: {len(documents[0].page_content)} caractères")
        
        print("\n2️⃣ Découpage en chunks...")
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=50)
        chunks = text_splitter.split_documents(documents)
        print(f"   ✅ {len(chunks)} chunks créés")
        
        print("\n3️⃣ Création des embeddings...")
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        print("   ✅ Modèle d'embeddings chargé")
        
        print("\n4️⃣ Création de la base vectorielle...")
        with tempfile.TemporaryDirectory() as temp_dir:
            vectorstore = Chroma.from_documents(
                documents=chunks,
                embedding=embeddings,
                persist_directory=temp_dir
            )
            print("   ✅ Base vectorielle créée")
            
            print("\n5️⃣ Initialisation du LLM...")
            llm = Ollama(model="mistral", temperature=0.7)
            print("   ✅ LLM initialisé")
            
            print("\n6️⃣ Test de requête...")
            qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                retriever=vectorstore.as_retriever(search_kwargs={"k": 2}),
                return_source_documents=True
            )
            
            question = "Quelle est la commande pour déployer l'application ?"
            print(f"\n   Question: {question}")
            print("   Génération de la réponse...")
            
            result = qa_chain({"query": question})
            
            print(f"\n   💡 Réponse: {result['result']}")
            print("\n✅ TEST RÉUSSI! Le système RAG fonctionne correctement!")
        
        # Nettoyer
        os.unlink(temp_file)
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur durant le test: {e}")
        print("\n💡 Vérifiez que:")
        print("  1. Ollama est en cours d'exécution")
        print("  2. Le modèle 'mistral' est installé")
        print("  3. Toutes les dépendances sont installées")
        return False


def main():
    """Fonction principale"""
    print("=" * 60)
    print("🧪 TEST DU SYSTÈME RAG")
    print("=" * 60)
    
    # 1. Vérifier les imports
    if not check_imports():
        sys.exit(1)
    
    # 2. Vérifier Ollama
    if not check_ollama():
        sys.exit(1)
    
    # 3. Vérifier les embeddings
    if not check_embeddings():
        sys.exit(1)
    
    # 4. Test complet
    print("\n" + "=" * 60)
    print("🚀 LANCEMENT DU TEST COMPLET")
    print("=" * 60)
    
    choice = input("\nVoulez-vous tester le système complet? (peut prendre 1-2 min) [o/N]: ")
    
    if choice.lower() in ['o', 'oui', 'y', 'yes']:
        if test_simple_rag():
            print("\n" + "=" * 60)
            print("🎉 TOUS LES TESTS SONT RÉUSSIS!")
            print("=" * 60)
            print("\n✅ Vous pouvez maintenant utiliser: python rag_system.py")
        else:
            sys.exit(1)
    else:
        print("\n✅ Installation vérifiée avec succès!")
        print("Lancez le test complet quand vous voulez avec: python test_installation.py")


if __name__ == "__main__":
    main()
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_core.documents import Document

from config import TOP_K_CHUNKS, PROMPT_TEMPLATE


def chunk_document_source(doc: Document) -> str:
    """
    Chemin/nom de fichier source pour un chunk.

    LanceDB (intégration LangChain) stocke les métadonnées d'origine dans
    metadata['metadata'] ; Chroma les plaçait à la racine.
    """
    m = doc.metadata or {}
    src = m.get("source")
    if isinstance(src, str) and src:
        return src
    nested = m.get("metadata")
    if isinstance(nested, dict):
        s = nested.get("source")
        if isinstance(s, str) and s:
            return s
    return "Inconnu"


class RAGSystem:
    """
    Orchestre embeddings, vectorstore et LLM pour répondre à des questions
    basées sur des documents.
    """

    def __init__(self, vectorstore, llm):
        """
        Args:
            vectorstore: Base vectorielle LanceDB chargée.
            llm:         Modèle de langage Ollama initialisé.
        """
        self.vectorstore = vectorstore
        self.llm = llm
        self._qa_chain = None  # Chaîne créée une seule fois (lazy init)

    # ------------------------------------------------------------------
    # Chaîne QA
    # ------------------------------------------------------------------

    def _build_qa_chain(self) -> RetrievalQA:
        """Construit la chaîne RetrievalQA (appelée une seule fois)."""
        prompt = PromptTemplate(
            template=PROMPT_TEMPLATE,
            input_variables=["context", "question"],
        )
        return RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(
                search_kwargs={"k": TOP_K_CHUNKS}
            ),
            return_source_documents=True,
            chain_type_kwargs={"prompt": prompt},
        )

    @property
    def qa_chain(self) -> RetrievalQA:
        """Lazy initialization de la chaîne QA."""
        if self._qa_chain is None:
            self._qa_chain = self._build_qa_chain()
        return self._qa_chain

    def reset_qa_chain(self) -> None:
        """À appeler après remplacement du vectorstore (réindexation)."""
        self._qa_chain = None

    # ------------------------------------------------------------------
    # Requête
    # ------------------------------------------------------------------

    def query(self, question: str, show_sources: bool = True) -> dict:
        """
        Pose une question au système RAG.

        Args:
            question:     La question de l'utilisateur.
            show_sources: Afficher les chunks sources dans la console.

        Returns:
            Dictionnaire LangChain contenant 'result' et 'source_documents'.
        """
        print(f"\n❓ Question : {question}")
        print("🤔 Recherche dans la documentation...")

        result = self.qa_chain.invoke({"query": question})

        print(f"\n💡 Réponse :\n{result['result']}")

        if show_sources and "source_documents" in result:
            print("\n📚 Sources utilisées :")
            for i, doc in enumerate(result["source_documents"], 1):
                source = chunk_document_source(doc)
                print(f"  {i}. {source}")
                print(f"     ↳ {doc.page_content[:200].strip()}...")

        return result
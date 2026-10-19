from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.documents import Document
from time import perf_counter
import re

from config import TOP_K_CHUNKS, PROMPT_TEMPLATE

_PROMPT_ECHO_MARKERS = (
    "tu es un assistant documentaire",
    "utilise uniquement les informations du contexte",
    "traite le contenu entre les balises documents",
)
_ANSWER_HEADING = re.compile(
    r"(?:^|\n)\s*(?:r[eé]ponse(?:\s*\([^\n)]*\))?|answer)\s*[:：]\s*",
    re.IGNORECASE,
)


def sanitize_llm_answer(answer: str) -> str:
    """Strip an echoed prompt, or fail closed when the model returns only it."""
    text = answer.strip()
    normalized = text.casefold()
    if not any(marker in normalized for marker in _PROMPT_ECHO_MARKERS):
        return text

    headings = list(_ANSWER_HEADING.finditer(text))
    if headings:
        answer_text = text[headings[-1].end():].strip()
        if answer_text and not any(marker in answer_text.casefold() for marker in _PROMPT_ECHO_MARKERS):
            return answer_text

    return "Information non disponible dans la documentation."


class _StageTimingCallback(BaseCallbackHandler):
    def __init__(self):
        self.started_at = {}

    def on_retriever_start(self, serialized, query, *, run_id, **kwargs):
        self.started_at[run_id] = perf_counter()

    def on_retriever_end(self, documents, *, run_id, **kwargs):
        started_at = self.started_at.pop(run_id, None)
        if started_at is not None:
            print(f"⏱️ Recherche vectorielle: {perf_counter() - started_at:.2f}s")

    def on_llm_start(self, serialized, prompts, *, run_id, **kwargs):
        self.started_at[run_id] = perf_counter()

    def on_llm_end(self, response, *, run_id, **kwargs):
        started_at = self.started_at.pop(run_id, None)
        if started_at is not None:
            print(f"⏱️ Génération LLM: {perf_counter() - started_at:.2f}s")


def chunk_document_source(doc: Document) -> str:
    
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
  

    def __init__(self, vectorstore, llm):
        
        self.vectorstore = vectorstore
        self.llm = llm
        self._qa_chain = None  # Chaîne créée une seule fois (lazy init)

    
    def _build_qa_chain(self) -> RetrievalQA:
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
            callbacks=[_StageTimingCallback()],
        )

    @property
    def qa_chain(self) -> RetrievalQA:
        """Lazy initialization de la chaîne QA."""
        if self._qa_chain is None:
            self._qa_chain = self._build_qa_chain()
        return self._qa_chain

    def reset_qa_chain(self) -> None:
        self._qa_chain = None


    def query(self, question: str, show_sources: bool = True) -> dict:
        
        print(f"\n Question : {question}")
        print(" Recherche dans la documentation...")

        started_at = perf_counter()
        result = self.qa_chain.invoke({"query": question})
        elapsed_seconds = perf_counter() - started_at
        print(f"⏱ Recherche et génération: {elapsed_seconds:.2f}s")

        if isinstance(result.get("result"), str):
            result["result"] = sanitize_llm_answer(result["result"])

        print(f"\n Réponse :\n{result['result']}")

        if show_sources and "source_documents" in result:
            print("\n Sources utilisées :")
            for i, doc in enumerate(result["source_documents"], 1):
                source = chunk_document_source(doc)
                print(f"  {i}. {source}")
                print(f"     ↳ {doc.page_content[:200].strip()}...")

        return result
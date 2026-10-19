from langchain_community.llms import Ollama
from config import LLM_MODEL, LLM_BASE_URL, LLM_TEMPERATURE, LLM_NUM_PREDICT


def get_llm(model_name: str = LLM_MODEL) -> Ollama:
    
    print(f" Initialisation du modèle LLM ({model_name})...")
    return Ollama(
        model=model_name,
        base_url=LLM_BASE_URL,
        temperature=LLM_TEMPERATURE,
        num_predict=LLM_NUM_PREDICT,
    )
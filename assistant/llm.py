from langchain_ollama import ChatOllama
from ollama import Client

from assistant import config


def ollama_headers() -> dict:
    return {"Authorization": f"Bearer {config.OLLAMA_API_KEY}"}


def get_llm() -> ChatOllama:
    return ChatOllama(
        model=config.MODEL,
        temperature=config.TEMPERATURE,
        reasoning=False,  # mode berpikir tidak menambah ketepatan, tetapi jauh lebih lambat
        base_url=config.OLLAMA_CLOUD_URL,
        client_kwargs={"headers": ollama_headers()},
    )


def get_ollama_client() -> Client:
    return Client(host=config.OLLAMA_CLOUD_URL, headers=ollama_headers())

from google import genai
from langchain_google_genai import ChatGoogleGenerativeAI

from assistant import config


def get_llm() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=config.MODEL,
        thinking_level=config.THINKING_LEVEL,
        google_api_key=config.GOOGLE_API_KEY,
    )


def get_google_client() -> genai.Client:
    return genai.Client(api_key=config.GOOGLE_API_KEY)

import io
from pathlib import Path

import pypdfium2

from assistant import config
from assistant.llm import get_ollama_client
from assistant.prompts import READ_PAGE_PROMPT


def render_page(pdf: Path, page_number: int) -> bytes:
    document = pypdfium2.PdfDocument(pdf)
    image = document[page_number - 1].render(scale=config.PAGE_RENDER_SCALE).to_pil()
    document.close()
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def read_page(image: bytes) -> str:
    response = get_ollama_client().chat(
        model=config.MODEL,
        think=False,
        options={"temperature": config.TEMPERATURE, "num_predict": config.PAGE_MAX_TOKENS},
        messages=[{"role": "user", "content": READ_PAGE_PROMPT, "images": [image]}],
    )
    return response.message.content.strip()

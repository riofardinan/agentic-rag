import io
from pathlib import Path

import pypdfium2
from google.genai import types

from assistant import config
from assistant.llm import get_google_client
from assistant.prompts import READ_PAGE_PROMPT


def render_page(pdf: Path, page_number: int) -> bytes:
    document = pypdfium2.PdfDocument(pdf)
    image = document[page_number - 1].render(scale=config.PAGE_RENDER_SCALE).to_pil()
    document.close()
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def read_page(image: bytes) -> str:
    # Client disimpan di variabel. Client yang tidak disimpan langsung ditutup sebelum request dikirim.
    client = get_google_client()
    response = client.models.generate_content(
        model=config.MODEL,
        contents=[types.Part.from_bytes(data=image, mime_type="image/png"), READ_PAGE_PROMPT],
        config=types.GenerateContentConfig(
            max_output_tokens=config.PAGE_MAX_TOKENS,
            thinking_config=types.ThinkingConfig(thinking_level=config.THINKING_LEVEL),
        ),
    )
    return response.text.strip()

import re

from google.genai import types
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_qdrant import FastEmbedSparse, QdrantVectorStore, RetrievalMode
from langchain_text_splitters import RecursiveCharacterTextSplitter

from assistant import config, documents
from assistant.llm import get_google_client

STRUCK_TEXT = re.compile(r"~~.*?~~", re.DOTALL)

# Gemini Embedding 2 tidak memakai pengaturan task_type. Jenis tugas ditulis sebagai awalan teks
# sesuai dokumentasi Google. Potongan dokumen dikirim tanpa judul ("title: none").
QUERY_PREFIX = "task: search result | query: "
DOCUMENT_PREFIX = "title: none | text: "


class GeminiEmbeddings(Embeddings):

    def __init__(self):
        self.client = get_google_client()

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        # Satu Content untuk setiap teks. Daftar string biasa akan digabung menjadi satu embedding.
        contents = [types.Content(parts=[types.Part(text=text)]) for text in texts]
        response = self.client.models.embed_content(model=config.EMBEDDING_MODEL, contents=contents)
        return [embedding.values for embedding in response.embeddings]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.embed_texts([DOCUMENT_PREFIX + text for text in texts])

    def embed_query(self, text: str) -> list[float]:
        return self.embed_texts([QUERY_PREFIX + text])[0]


def clean_text(text: str) -> str:
    # Teks yang dicoret sudah tidak berlaku, dan LLM sering salah membaca tanda ~~coret~~
    return STRUCK_TEXT.sub("", text)


def load_pages() -> list[Document]:
    pages = []
    for pdf in documents.list_pdfs():
        metadata = {
            "title": documents.title(pdf),
            "department": pdf.parent.name,
            "document": documents.relative_path(pdf),
        }
        for page_number in range(1, documents.page_count(pdf) + 1):
            text = documents.page_file(pdf, page_number).read_text(encoding="utf-8")
            pages.append(Document(page_content=clean_text(text), metadata={**metadata, "page": page_number}))
    return pages


def split_pages(pages: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=config.CHUNK_SIZE, chunk_overlap=config.CHUNK_OVERLAP)
    return [chunk for chunk in splitter.split_documents(pages) if len(chunk.page_content) >= config.MIN_CHUNK_LENGTH]


def index_settings() -> dict:
    # Hybrid search: makna (embedding Gemini) digabung dengan kata kunci (BM25)
    return {
        "embedding": GeminiEmbeddings(),
        "sparse_embedding": FastEmbedSparse(model_name=config.SPARSE_MODEL),
        "retrieval_mode": RetrievalMode.HYBRID,
        "path": str(config.INDEX_DIR),
        "collection_name": config.COLLECTION_NAME,
    }


def build_index(chunks: list[Document]):
    QdrantVectorStore.from_documents(chunks, **index_settings(), force_recreate=True)


def load_index() -> QdrantVectorStore:
    return QdrantVectorStore.from_existing_collection(**index_settings())

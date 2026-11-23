import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# Model Gemini API yang sama dipakai untuk menjawab pertanyaan dan membaca halaman dokumen
MODEL = "gemini-3.5-flash-lite"
THINKING_LEVEL = "minimal"  # mode berpikir dimatikan: tidak menambah ketepatan, tetapi jauh lebih lambat
PAGE_MAX_TOKENS = 4096  # batas panjang hasil baca satu halaman

# Membaca dokumen: halaman PDF diubah menjadi gambar sebelum dibaca model
PAGE_RENDER_SCALE = 2  # 2 x 72 dpi = 144 dpi, cukup tajam untuk teks kecil dan tabel

# Indeks dan pencarian
EMBEDDING_MODEL = "gemini-embedding-2"  # lewat Gemini API (Google)
SPARSE_MODEL = "Qdrant/bm25"
COLLECTION_NAME = "documents"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
MIN_CHUNK_LENGTH = 100  # potongan yang lebih pendek biasanya hanya header atau footer halaman
SEARCH_RESULTS = 4
MAX_REWRITES = 2

# Folder "Regulasi" berisi peraturan pemerintah, folder lain berisi dokumen perusahaan
REGULATION_FOLDER = "Regulasi"

# Dokumen rahasia: lokasi file -> departemen yang boleh membaca. Dokumen lain boleh dibaca semua karyawan.
CONFIDENTIAL_DOCUMENTS = {
    "HR/Struktur Gaji dan Grade 2026.pdf": ["People & Culture"],
}

CHAT_TITLE_LENGTH = 40  # panjang maksimal judul percakapan di daftar riwayat

# Akun demo. Di aplikasi perusahaan sungguhan, identitas ini berasal dari login kantor (SSO).
DEMO_EMPLOYEE_ID = "EMP001"

DATA_DIR = Path(__file__).parent.parent / "data"
DOCUMENTS_DIR = DATA_DIR / "documents"
PAGES_DIR = DATA_DIR / "pages"
INDEX_DIR = DATA_DIR / "index"
DATABASE_PATH = DATA_DIR / "company.db"

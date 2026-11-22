from assistant import config, knowledge

try:
    pages = knowledge.load_pages()
except FileNotFoundError as error:
    raise SystemExit(f"Halaman belum dibaca: {error.filename}\nJalankan dulu: python read_documents.py")

chunks = knowledge.split_pages(pages)
print(f"{len(pages)} halaman dipotong menjadi {len(chunks)} potongan. Membuat embedding...")
knowledge.build_index(chunks)
print(f"Indeks tersimpan di {config.INDEX_DIR}")

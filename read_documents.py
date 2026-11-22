from assistant import documents, reader

# Setiap halaman PDF dibaca model visi menjadi Markdown, lalu disimpan di data/pages.
# Halaman yang sudah dibaca dilewati, jadi skrip ini aman dijalankan ulang jika terhenti.
for pdf in documents.list_pdfs():
    for page_number in range(1, documents.page_count(pdf) + 1):
        page_file = documents.page_file(pdf, page_number)
        if page_file.exists():
            continue

        text = reader.read_page(reader.render_page(pdf, page_number))
        page_file.parent.mkdir(parents=True, exist_ok=True)
        page_file.write_text(text, encoding="utf-8")
        print(f"Dibaca: {documents.relative_path(pdf)} hal. {page_number}")

print("Semua halaman sudah dibaca.")

# AI Knowledge Assistant

Asisten chat berbasis **Agentic RAG** untuk karyawan Nusa Teknologi (perusahaan fiktif). Asisten ini menjawab pertanyaan dari dokumen perusahaan dan cuplikan PP Nomor 35 Tahun 2021 beserta sumbernya, mengecek dan mengajukan cuti dengan konfirmasi, serta membuat tiket IT.

Link: https://assistant-knowledge-agentic-rag.streamlit.app/

## Cara Menjalankan

**1. Siapkan virtual environment** (Python 3.12)

```bash
python3.12 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**2. Buat file `.env`**

```bash
cp .env.example .env
```

Isi `GOOGLE_API_KEY` dari [aistudio.google.com/apikey](https://aistudio.google.com/apikey).

**3. Baca dokumen** (sekali, atau setiap kali dokumen berubah)

```bash
python read_documents.py
```

Setiap halaman PDF di `data/documents` dibaca model visi lalu disimpan sebagai Markdown di `data/pages`. Jika terhenti, jalankan lagi: halaman yang sudah dibaca dilewati.

**4. Buat indeks** (setelah langkah 3)

```bash
python build_index.py
```

Paket gratis Gemini API membatasi 100 teks per menit. Jika muncul error `429 RESOURCE_EXHAUSTED`, tunggu satu menit lalu jalankan lagi.

**5. Jalankan aplikasi**

```bash
streamlit run app.py
```

Untuk menguji lewat terminal, jalankan `python chat.py`, atau `python chat.py EMP002` untuk masuk sebagai akun lain.

## Dokumen

| Folder | Dokumen |
|---|---|
| HR | Peraturan Perusahaan 2026-2027, SOP Cuti dan Izin, Kebijakan Kerja Hybrid, Struktur Gaji dan Grade 2026 (rahasia), Buku Saku Karyawan Baru |
| Finance | Kebijakan Reimbursement dan Perjalanan Dinas Rev. 02 |
| Regulasi | Cuplikan PP Nomor 35 Tahun 2021: halaman judul dan Bab IV Waktu Kerja dan Waktu Istirahat (halaman 1 dan 14–21 dokumen asli) |

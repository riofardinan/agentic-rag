# AI Knowledge Assistant v2

Asisten chat berbasis **Agentic RAG** untuk karyawan Nusa Teknologi (perusahaan fiktif). Asisten ini menjawab pertanyaan dari dokumen perusahaan dan cuplikan PP Nomor 35 Tahun 2021 beserta sumbernya, mengecek dan mengajukan cuti dengan konfirmasi, serta membuat tiket IT.

## Yang Berubah dari v1

Stack v2 dipilih dari hasil benchmark di `../_scratchpad/HASIL.md` (rata-rata 25,5 dari 32, versi v1: 12,5).

| Bagian | v1 | v2 |
|---|---|---|
| Membaca PDF | `pypdf` (hanya teks digital) | Model visi membaca setiap halaman menjadi Markdown, termasuk scan, tabel, grafik, dan bagan |
| Teks yang dicoret | Ikut terbaca | Dibuang sebelum diindeks |
| Potongan | 400 karakter | 800 karakter |
| Embedding | MiniLM (lokal) | Gemini Embedding 2 (Gemini API) |
| Indeks | Dibangun ulang di memori setiap aplikasi dinyalakan | Dibangun sekali, disimpan di `data/index` |
| Prompt | Aturan 1–10 | Ditambah aturan 11 (selalu cari dulu) |
| Hak akses | Semua dokumen terbaca semua akun | Dokumen rahasia hanya untuk departemen tertentu (`CONFIDENTIAL_DOCUMENTS` di `assistant/config.py`) |
| Mode LLM | Ollama Cloud atau Ollama lokal | Ollama Cloud saja. Tidak ada model besar yang dijalankan di laptop |
| Percakapan | Hilang saat aplikasi ditutup, tidak ada daftar riwayat | Tersimpan di SQLite. Sidebar mirip ChatGPT: percakapan baru, riwayat, dan profil |

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

Isi dua API key:

- `OLLAMA_API_KEY` dari [ollama.com/settings/keys](https://ollama.com/settings/keys), untuk membaca dokumen dan menjawab pertanyaan;
- `GOOGLE_API_KEY` dari [aistudio.google.com/apikey](https://aistudio.google.com/apikey), untuk embedding.

**3. Baca dokumen** (sekali, atau setiap kali dokumen berubah)

```bash
python read_documents.py
```

Setiap halaman PDF di `data/documents` dibaca model visi lalu disimpan sebagai Markdown di `data/pages`. Untuk 41 halaman, prosesnya sekitar 3 menit. Jika terhenti, jalankan lagi: halaman yang sudah dibaca dilewati.

**4. Buat indeks** (setelah langkah 3)

```bash
python build_index.py
```

Setiap potongan dokumen dikirim ke Gemini API untuk dibuat embedding-nya. 41 halaman menjadi 98 potongan, dan prosesnya sekitar 10 detik dengan memori sekitar 200 MB.

Paket gratis Gemini API membatasi 100 teks per menit dan 1.000 teks per hari, dan korpus ini sengaja dibuat di bawah batas per menit. Jika muncul error `429 RESOURCE_EXHAUSTED`, berarti batas itu terlewati: tunggu satu menit (atau sampai besok untuk batas harian), lalu jalankan lagi.

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

Dokumen tambahan untuk capstone ada di `../capstone` dan tidak ikut diindeks.

## Akun Demo

| ID | Nama | Departemen | Catatan |
|---|---|---|---|
| EMP001 | Budi Santoso | Engineering | Tidak bisa membaca dokumen struktur gaji |
| EMP002 | Rina Wulandari | People & Culture | Bisa membaca dokumen struktur gaji |

Akun diganti lewat profil di bagian bawah sidebar. Setiap akun punya riwayat percakapannya sendiri.

## Catatan

- **Riwayat percakapan disimpan di `data/company.db`**, termasuk memori agent (`SqliteSaver`). Percakapan lama bisa dibuka dari sidebar dan dilanjutkan. Di Streamlit Community Cloud, file ini kembali kosong setiap kali aplikasi dinyalakan ulang, sehingga riwayat, pengajuan cuti, dan tiket IT ikut hilang.
- **Indeks hanya bisa dibuka satu program sekaligus.** Tutup `app.py` sebelum menjalankan `chat.py` atau `build_index.py`, dan sebaliknya.
- **Tidak butuh GPU.** Model visi, LLM, dan embedding berjalan di cloud. Yang berjalan di laptop hanya BM25 (model sekitar 10 MB), indeks Qdrant, dan database SQLite.
- **Isi dokumen dikirim ke Ollama Cloud dan Gemini API**, baik saat membaca dokumen, membuat indeks, maupun menjawab. Konten yang dikirim lewat paket gratis Gemini API dipakai Google untuk memperbaiki produknya. Ini aman untuk dokumen fiktif di proyek ini. Untuk data asli perusahaan, pakai layanan berbayar atau model yang dijalankan di server sendiri.
- **Model cloud bisa dipensiunkan penyedianya.** Nama model hanya ditulis di `assistant/config.py` (`MODEL` dan `EMBEDDING_MODEL`), jadi cukup diganti di sana. Setelah mengganti model embedding, jalankan ulang `build_index.py`.

## Struktur Folder

```
codev2/
├── app.py               # UI chat Streamlit
├── chat.py              # versi terminal
├── read_documents.py    # PDF -> Markdown per halaman (model visi)
├── build_index.py       # Markdown -> indeks pencarian
├── data/
│   ├── documents/       # PDF per departemen (HR, Finance, Regulasi)
│   ├── pages/           # hasil baca per halaman
│   └── index/           # indeks pencarian (dibuat build_index.py)
└── assistant/
    ├── config.py        # semua pengaturan
    ├── prompts.py       # semua prompt
    ├── llm.py           # koneksi ke Ollama Cloud
    ├── documents.py     # lokasi file PDF dan halaman
    ├── reader.py        # membaca satu halaman dengan model visi
    ├── knowledge.py     # memotong, embedding (Gemini API), dan indeks
    ├── database.py      # data karyawan, cuti, dan tiket IT
    ├── tools.py         # tool agent dan filter hak akses
    └── graph.py         # alur Agentic RAG
```

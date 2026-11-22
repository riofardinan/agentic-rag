READ_PAGE_PROMPT = """Ubah halaman dokumen pada gambar ini menjadi Markdown.
Aturan:
1. Tulis semua teks apa adanya, termasuk judul, header, footer, nomor halaman, dan catatan kaki kecil.
2. Tulis tabel sebagai tabel Markdown. Jika ada sel gabungan, ulangi isinya di setiap baris atau kolom yang dicakup.
3. Teks yang dicoret tulis sebagai ~~teks~~.
4. Untuk bagan, diagram alur, grafik, kalender berwarna, atau gambar lain, jelaskan isinya dalam kalimat: semua label dan angka, arti warna menurut legenda, dan hubungan antarkotak (siapa melapor kepada siapa, urutan langkah, arah panah).
5. Tulisan tangan, paraf, cap, dan tanda tangan: tulis isinya jika terbaca, misalnya [tulisan tangan: ...] atau [cap: ...].
6. Jangan menambah informasi, tautan, atau gambar yang tidak ada di halaman. Balas hanya dengan Markdown."""

SYSTEM_PROMPT = """Kamu adalah AI Knowledge Assistant untuk karyawan Nusa Teknologi.
Kamu sedang membantu {name} ({position}, departemen {department}).
Hari ini {day}, {today}.

Aturan:
1. Untuk pertanyaan tentang aturan, kebijakan, fasilitas, atau prosedur perusahaan, selalu cari dulu dengan tool search_documents. Jangan menjawab dari pengetahuanmu sendiri.
2. Jawab hanya berdasarkan hasil pencarian, lalu sebutkan sumbernya. Contoh: (Sumber: SOP Cuti dan Izin, hal. 1).
3. Jika hasil pencarian tidak memuat jawabannya, katakan bahwa informasi itu tidak ada di dokumen perusahaan dan sarankan menghubungi HR.
4. Jika permintaan kurang jelas, tanyakan dulu. Contoh: jenis cuti atau tanggal cuti belum disebutkan.
5. Tool request_leave hanya untuk cuti tahunan dan hanya dipanggil jika tanggal mulai, tanggal selesai, dan alasan sudah jelas.
6. Saat memanggil tool, jangan menulis teks jawaban. Panggil semua tool yang dibutuhkan sekaligus, lalu tulis jawaban setelah semua hasil tool diterima. Jangan memanggil ulang tool yang hasilnya sudah ada.
7. Untuk aturan kantor, cari di sumber "internal". Jika pertanyaan tidak menyebut peraturan pemerintah, anggap yang ditanyakan adalah aturan kantor yang berlaku untuk karyawan. Untuk ketentuan pemerintah, cari di sumber "regulasi". Untuk membandingkan aturan kantor dengan regulasi, lakukan dua pencarian terpisah (internal dan regulasi) dengan kata kunci yang spesifik, lalu bandingkan.
8. Setiap kali menjelaskan regulasi pemerintah, tambahkan catatan singkat bahwa jawaban ini bukan nasihat hukum.
9. Tolak dengan sopan pertanyaan yang tidak berhubungan dengan pekerjaan di Nusa Teknologi.
10. Jawab dalam bahasa Indonesia yang singkat dan ramah.
11. Pertanyaan apa pun tentang perusahaan, termasuk angka, data layanan, jadwal, kalender, dan struktur organisasi, wajib dicari dulu dengan search_documents sebelum menjawab."""

GRADE_PROMPT = """Kamu menilai hasil pencarian dokumen perusahaan.

Kata kunci pencarian: {query}

Hasil pencarian:
{documents}

Apakah hasil pencarian berisi informasi untuk menjawab kata kunci pencarian?"""

REWRITE_PROMPT = """Pencarian dokumen perusahaan dengan kata kunci "{query}" tidak menemukan hasil yang relevan.
Tulis kata kunci pencarian baru dalam bahasa Indonesia baku. Ganti istilah asing atau singkatan dengan padanannya.
Balas hanya dengan kata kunci baru."""

SEARCH_TOOL_DESCRIPTION = """Cari informasi di dokumen. Pilih satu sumber untuk setiap pencarian:
- "internal": semua dokumen perusahaan, yaitu Peraturan Perusahaan (jam kerja, keterlambatan, lembur, upah, THR, tata tertib, sanksi), SOP Cuti dan Izin, Kebijakan Kerja Hybrid, Kebijakan Reimbursement dan Perjalanan Dinas, Struktur Gaji dan Grade, dan Buku Saku Karyawan Baru (fasilitas kantor dan tugas karyawan baru).
- "regulasi": peraturan pemerintah, yaitu cuplikan PP Nomor 35 Tahun 2021 bab waktu kerja dan waktu istirahat (jam kerja, istirahat, lembur, upah lembur)."""

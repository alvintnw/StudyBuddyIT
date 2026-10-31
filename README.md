# StudyBuddy IT

Chatbot asisten belajar berbasis AI untuk mahasiswa Teknik Informatika.
Dibuat sebagai Final Project **AI Productivity and AI API Integration for Developers** (Hacktiv8).

## Use Case
Mahasiswa Informatika sering butuh penjelasan konsep, latihan soal, bantuan debugging, dan rencana belajar di luar jam kuliah. StudyBuddy IT menjawab kebutuhan tersebut dengan model LLM (Google Gemini) yang diatur lewat beberapa parameter kreatif.

## Fitur
| Fitur | Keterangan |
|---|---|
| **Gaya bahasa** | Pilih Santai (kakak tingkat) atau Formal (dosen) |
| **Mode belajar** | Jelaskan Konsep, Latihan Soal, Debug Kode, Rencana Belajar |
| **Domain khusus** | Fokus pada topik informatika; pertanyaan di luar topik diarahkan kembali |
| **Memory** | Riwayat percakapan (12 pesan terakhir) + profil pengguna (nama, semester, topik fokus) disisipkan ke system prompt |
| **Rekomendasi** | 3 pertanyaan lanjutan otomatis setelah setiap jawaban |
| **Kontrol kreativitas** | Slider temperature 0.0 - 1.5 |
| **Streaming** | Jawaban tampil bertahap |
| **Ekspor** | Unduh riwayat chat dalam format Markdown |

## Teknologi
- Python 3.10+
- [Streamlit](https://streamlit.io/) untuk antarmuka
- [Google Gemini API](https://ai.google.dev/) (`google-genai`) sebagai model bahasa

## Cara Menjalankan
```bash
git clone <URL-REPO>
cd <nama-folder>

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # lalu isi GEMINI_API_KEY
streamlit run app.py
```
API key gratis bisa dibuat di [Google AI Studio](https://aistudio.google.com/apikey). Jangan pernah meng-commit file `.env`.

## Struktur Proyek
```
.
├── app.py              # aplikasi utama (UI + logika chatbot)
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── screenshots/        # tangkapan layar UI
```

## Cara Kerja Singkat
1. Pengaturan sidebar (gaya, mode, profil) dirakit menjadi *system instruction* di `build_system_prompt()`.
2. Riwayat chat dipotong ke 12 pesan terakhir lalu dikirim ke Gemini (`stream_answer()`).
3. Setelah jawaban selesai, `get_suggestions()` meminta model membuat 3 pertanyaan lanjutan.

## Catatan
Chatbot ini alat bantu belajar, bukan pengganti dosen atau sumber resmi. Selalu verifikasi jawaban penting.

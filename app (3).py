"""
StudyBuddy IT - Chatbot asisten belajar untuk mahasiswa Informatika.
Final Project: AI Productivity and AI API Integration for Developers (Hacktiv8)

Stack: Streamlit (UI) + Google Gemini API (LLM)
"""

import os
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# ---------------------------------------------------------------------------
# Konfigurasi dasar
# ---------------------------------------------------------------------------
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
MAX_HISTORY_TURNS = 12  # jumlah pesan terakhir yang dikirim ke model (memory jangka pendek)

st.set_page_config(page_title="StudyBuddy IT", page_icon="🎓", layout="wide")

# ---------------------------------------------------------------------------
# Parameter kreatif: gaya bahasa dan mode belajar
# ---------------------------------------------------------------------------
STYLES = {
    "Santai": (
        "Gunakan Bahasa Indonesia santai dan ramah seperti kakak tingkat yang suportif. "
        "Boleh memakai sapaan 'kamu' dan analogi sehari-hari, tetapi tetap akurat."
    ),
    "Formal": (
        "Gunakan Bahasa Indonesia formal dan baku seperti dosen pembimbing. "
        "Struktur jawaban rapi, istilah teknis dijelaskan secara tepat."
    ),
}

MODES = {
    "Jelaskan Konsep": (
        "Jelaskan konsep dari dasar: definisi singkat, analogi, contoh konkret, "
        "lalu ringkasan poin penting. Sesuaikan kedalaman dengan level pengguna."
    ),
    "Latihan Soal": (
        "Berperan sebagai pemberi latihan. Buat soal bertahap (mudah ke sulit) tentang topik "
        "yang diminta, satu per satu. Jangan langsung beri kunci jawaban; beri petunjuk dulu, "
        "lalu bahas jawaban setelah pengguna mencoba."
    ),
    "Debug Kode": (
        "Bantu debugging: identifikasi akar masalah, jelaskan penyebabnya, tunjukkan kode "
        "perbaikan dalam blok kode, dan beri tips agar tidak terulang."
    ),
    "Rencana Belajar": (
        "Susun rencana belajar realistis dengan jadwal, prioritas topik, dan sumber belajar "
        "yang disarankan, sesuai waktu yang dimiliki pengguna."
    ),
}


def build_system_prompt(style: str, mode: str, profile: dict) -> str:
    """Menggabungkan persona, mode, dan memory profil menjadi satu system instruction."""
    profile_lines = []
    if profile["nama"]:
        profile_lines.append(f"- Nama pengguna: {profile['nama']}")
    if profile["semester"]:
        profile_lines.append(f"- Semester: {profile['semester']}")
    if profile["fokus"]:
        profile_lines.append(f"- Topik yang sedang dipelajari: {profile['fokus']}")
    profile_text = "\n".join(profile_lines) if profile_lines else "- (belum diisi)"

    return f"""Kamu adalah StudyBuddy IT, asisten belajar AI untuk mahasiswa Teknik Informatika.
Cakupan keahlian: pemrograman, struktur data & algoritma, basis data, jaringan, machine learning,
rekayasa perangkat lunak, dan pengembangan web.

GAYA BAHASA:
{STYLES[style]}

MODE SAAT INI ({mode}):
{MODES[mode]}

PROFIL PENGGUNA (memory):
{profile_text}

ATURAN:
- Jawab dalam Bahasa Indonesia kecuali pengguna meminta bahasa lain.
- Jika pertanyaan di luar topik informatika/akademik, arahkan kembali dengan sopan.
- Jika tidak yakin, katakan terus terang; jangan mengarang fakta atau sumber.
- Jangan mengerjakan tugas/ujian secara utuh untuk dikumpulkan; bantu pengguna memahami.
- Gunakan format Markdown dan blok kode bila ada kode.
"""


# ---------------------------------------------------------------------------
# Pemanggilan API
# ---------------------------------------------------------------------------
@st.cache_resource
def get_client(api_key: str) -> genai.Client:
    return genai.Client(api_key=api_key)


def to_contents(messages: list[dict]) -> list[types.Content]:
    """Ubah riwayat chat Streamlit menjadi format Content Gemini."""
    contents = []
    for m in messages[-MAX_HISTORY_TURNS:]:
        role = "user" if m["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part(text=m["content"])]))
    return contents


def stream_answer(client, system_prompt: str, messages: list[dict], temperature: float):
    """Streaming jawaban dari model."""
    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        temperature=temperature,
        max_output_tokens=2048,
    )
    for chunk in client.models.generate_content_stream(
        model=MODEL_NAME, contents=to_contents(messages), config=config
    ):
        if chunk.text:
            yield chunk.text


def get_suggestions(client, question: str, answer: str) -> list[str]:
    """Fitur rekomendasi: 3 pertanyaan lanjutan berdasarkan percakapan terakhir."""
    prompt = (
        "Berdasarkan percakapan berikut, buat 3 pertanyaan lanjutan singkat (maks 12 kata) "
        "yang relevan untuk mahasiswa. Tulis satu pertanyaan per baris, tanpa nomor.\n\n"
        f"Pertanyaan: {question}\n\nJawaban: {answer[:1500]}"
    )
    try:
        resp = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.7, max_output_tokens=200),
        )
        lines = [l.strip(" -*•\t") for l in (resp.text or "").splitlines() if l.strip()]
        return lines[:3]
    except Exception:
        return []


def export_markdown(messages: list[dict]) -> str:
    out = [f"# Riwayat Chat StudyBuddy IT\n_Diekspor {datetime.now():%d %b %Y %H:%M}_\n"]
    for m in messages:
        who = "Kamu" if m["role"] == "user" else "StudyBuddy"
        out.append(f"**{who}:**\n\n{m['content']}\n")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "suggestions" not in st.session_state:
    st.session_state.suggestions = []
if "pending" not in st.session_state:
    st.session_state.pending = None

# ---------------------------------------------------------------------------
# Sidebar: pengaturan
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("🎓 StudyBuddy IT")
    st.caption("Asisten belajar untuk mahasiswa Informatika")

    api_key = os.getenv("GEMINI_API_KEY") or st.text_input(
        "Gemini API Key", type="password", help="Atau isi GEMINI_API_KEY di file .env"
    )

    st.subheader("⚙️ Pengaturan")
    style = st.radio("Gaya bahasa", list(STYLES.keys()), horizontal=True)
    mode = st.selectbox("Mode belajar", list(MODES.keys()))
    temperature = st.slider("Kreativitas (temperature)", 0.0, 1.5, 0.7, 0.1)

    st.subheader("🧠 Memory profil")
    profile = {
        "nama": st.text_input("Nama panggilan"),
        "semester": st.text_input("Semester", placeholder="mis. 5"),
        "fokus": st.text_input("Topik fokus", placeholder="mis. Machine Learning"),
    }

    st.divider()
    col1, col2 = st.columns(2)
    if col1.button("🗑️ Reset chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.suggestions = []
        st.rerun()
    if st.session_state.messages:
        col2.download_button(
            "💾 Ekspor",
            export_markdown(st.session_state.messages),
            file_name="riwayat_chat.md",
            use_container_width=True,
        )

# ---------------------------------------------------------------------------
# Halaman utama
# ---------------------------------------------------------------------------
st.header("Tanya apa saja seputar Informatika 💻")

if not st.session_state.messages:
    st.info(
        "Halo! Aku StudyBuddy IT. Pilih gaya bahasa dan mode belajar di sidebar, "
        "lalu coba salah satu contoh di bawah atau ketik pertanyaanmu."
    )
    examples = [
        "Jelaskan perbedaan stack dan queue",
        "Apa itu overfitting pada machine learning?",
        "Buatkan latihan SQL JOIN",
    ]
    cols = st.columns(len(examples))
    for col, ex in zip(cols, examples):
        if col.button(ex, use_container_width=True):
            st.session_state.pending = ex
            st.rerun()

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Tombol rekomendasi pertanyaan lanjutan
if st.session_state.suggestions:
    st.caption("💡 Pertanyaan lanjutan yang mungkin kamu suka:")
    cols = st.columns(len(st.session_state.suggestions))
    for i, (col, s) in enumerate(zip(cols, st.session_state.suggestions)):
        if col.button(s, key=f"sug_{i}_{len(st.session_state.messages)}", use_container_width=True):
            st.session_state.pending = s
            st.rerun()

user_input = st.chat_input("Ketik pertanyaanmu di sini...")
if st.session_state.pending:
    user_input = st.session_state.pending
    st.session_state.pending = None

if user_input:
    if not api_key:
        st.error("Masukkan Gemini API Key di sidebar atau file .env terlebih dahulu.")
        st.stop()

    client = get_client(api_key)
    st.session_state.suggestions = []
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    system_prompt = build_system_prompt(style, mode, profile)
    with st.chat_message("assistant"):
        try:
            answer = st.write_stream(
                stream_answer(client, system_prompt, st.session_state.messages, temperature)
            )
        except Exception as e:
            answer = f"⚠️ Terjadi kesalahan saat menghubungi API: `{e}`"
            st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
    if not answer.startswith("⚠️"):
        st.session_state.suggestions = get_suggestions(client, user_input, answer)
    st.rerun()

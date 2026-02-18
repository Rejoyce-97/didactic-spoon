import os
import io
import math
import streamlit as st
from pypdf import PdfReader
from gtts import gTTS

# Optional OpenAI import
try:
    from openai import OpenAI
except Exception:
    OpenAI = None

st.set_page_config(page_title="AccessEd AI", layout="wide")

st.title("AccessEd AI — Learning without barriers")
st.write(
    "A mobile-first AI study assistant that helps students with disabilities "
    "by simplifying text and offering text-to-speech."
)

# -------------------------
# Helper functions
# -------------------------
def extract_text_from_pdf(file_bytes):
    reader = PdfReader(io.BytesIO(file_bytes))
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

def fallback_summary(text, max_chars=800):
    text = " ".join(text.split())
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "..."

def ai_summary(text):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return fallback_summary(text)

    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Summarize text in simple, clear language for students."},
            {"role": "user", "content": text},
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content

def create_audio(text):
    tts = gTTS(text=text, lang="en")
    audio_bytes = io.BytesIO()
    tts.write_to_fp(audio_bytes)
    return audio_bytes.getvalue()

def estimate_time_saved(original, summary):
    if original == 0 or summary == 0:
        return 0
    original_minutes = original / 200
    summary_minutes = summary / 200
    return max(0, round(original_minutes - summary_minutes))

# -------------------------
# Sidebar
# -------------------------
st.sidebar.header("Upload Study Material")

uploaded_file = st.sidebar.file_uploader("Upload PDF or TXT", type=["pdf", "txt"])
pasted_text = st.sidebar.text_area("Or paste text here")

st.sidebar.header("Accessibility Settings")
font_size = st.sidebar.slider("Font size", 14, 26, 18)
high_contrast = st.sidebar.checkbox("High contrast mode")

# -------------------------
# Styling
# -------------------------
bg_color = "#000000" if high_contrast else "#ffffff"
text_color = "#ffffff" if high_contrast else "#000000"

st.markdown(
    f"""
    <style>
        .stApp {{
            background-color: {bg_color};
            color: {text_color};
        }}
        * {{
            font-size: {font_size}px !important;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------
# Load text
# -------------------------
source_text = ""

if uploaded_file:
    if uploaded_file.type == "application/pdf":
        source_text = extract_text_from_pdf(uploaded_file.read())
    else:
        source_text = uploaded_file.read().decode("utf-8", errors="ignore")

if pasted_text.strip():
    source_text = pasted_text

if not source_text:
    st.info("Upload a file or paste text to get started.")
    st.stop()

# -------------------------
# Tabs
# -------------------------
tab1, tab2, tab3 = st.tabs(["✨ Simplify", "🔊 Listen", "📊 Impact"])

with tab1:
    st.subheader("Plain-language summary")
    if st.button("Generate Summary"):
        with st.spinner("Creating summary..."):
            summary = ai_summary(source_text)
            st.session_state["summary"] = summary

    st.text_area(
        "Summary",
        st.session_state.get("summary", ""),
        height=250
    )

with tab2:
    st.subheader("Text-to-Speech")
    if "summary" not in st.session_state:
        st.warning("Generate a summary first.")
    else:
        if st.button("Read Aloud"):
            audio = create_audio(st.session_state["summary"])
            st.audio(audio, format="audio/mp3")

with tab3:
    st.subheader("Measurable Impact")
    original_words = len(source_text.split())
    summary_words = len(st.session_state.get("summary", "").split())

    st.metric("Original words", original_words)
    st.metric("Summary words", summary_words)

    if summary_words > 0:
        minutes_saved = estimate_time_saved(original_words, summary_words)
        st.metric("Estimated study time saved (minutes)", minutes_saved)

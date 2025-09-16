# app.py
# --- AI Resume Critiquer Agent ---
# What it does:
# 1) Upload a PDF or TXT resume.
# 2) Optionally enter a target role and/or paste a job description.
# 3) Click "Analyze" to get structured, practical feedback.

import io
import os
import PyPDF2
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# Load .env (must contain OPENAI_API_KEY)
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()

# --- Page setup ---
st.set_page_config(page_title="AI Resume Critiquer", page_icon="📄", layout="centered")
st.title("AI Resume Critiquer 📄")
st.write("Upload your resume and get clear AI-powered feedback tailored to your needs!")

# --- Inputs ---
uploaded = st.file_uploader("Upload resume (PDF or TXT)", type=["pdf", "txt"])
job_role = st.text_input("Target role (optional)", placeholder="e.g., Backend Engineer")
job_desc = st.text_area("Job description (optional)", placeholder="Paste the job ad text here")

MODEL_NAME = "gpt-4o-mini"
TEMPERATURE = 0.6
MAX_TOKENS = 900

def extract_text(file) -> str:
    """Very simple text extraction: PDF pages concatenated or UTF-8 TXT."""
    if uploaded.type == "application/pdf":
        data = file.read()
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(data))
            text = ""
            for page in reader.pages:
                text += (page.extract_text() or "") + "\n"
            return text.strip()
        except Exception:
            return ""
    else:
        try:
            return file.read().decode("utf-8", errors="ignore").strip()
        except Exception:
            return ""

if st.button("Analyze"):
    # 1) Basic checks
    if not uploaded:
        st.error("Please upload a PDF or TXT file.")
        st.stop()

    if not OPENAI_API_KEY:
        st.error("OPENAI_API_KEY is missing. Create a .env file with your key before running.")
        st.info(
            "Example .env:\n\nOPENAI_API_KEY=sk-your-key-here",
            icon="ℹ️",
        )
        st.stop()

    # 2) Extract resume text
    with st.spinner("Reading your file..."):
        resume_text = extract_text(uploaded)

    if not resume_text:
        st.error("Could not extract text. If the PDF is scanned, export a text-based PDF.")
        st.stop()

    # 3) Build a simple, structured prompt
    target = job_role.strip() if job_role.strip() else "general applications"
    jd_part = f"\n\nJob Description:\n{job_desc.strip()}" if job_desc.strip() else ""

    system_msg = (
        "You are an expert resume reviewer. "
        "Give concise, practical feedback with concrete suggestions. Avoid fluff."
    )

    user_msg = f"""
Analyze the following resume and provide helpful, actionable feedback for **{target}**.

Respond in English, formatted in Markdown with these sections:

### Summary (2–3 sentences)

### Strengths
- 3–6 concise bullets

### Key Improvements
- 3–6 concise bullets (e.g., missing metrics/skills/clarity)

### Rewritten Bullets (examples)
For 3–6 items, show:
- **Before:** ...
- **After:** ...

### Role/ATS Alignment
- Top keywords already present
- Important missing/weak keywords (and natural ways to add them)

{jd_part}

### Resume Content
{resume_text}
    """.strip()

    # 4) Call the model
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        with st.spinner("Analyzing with AI..."):
            resp = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg},
                ],
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
            )

        content = resp.choices[0].message.content
        st.markdown("### Results")
        st.markdown(content)

        # Download button
        st.download_button(
            "Download results (Markdown)",
            data=content.encode("utf-8"),
            file_name="resume_feedback.md",
            mime="text/markdown",
        )

    except Exception as e:
        st.error(f"Error: {e}")
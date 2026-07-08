import streamlit as st
import pdfplumber
import docx2txt
import requests
import json
import os
import re
from dotenv import load_dotenv
from pdf2image import convert_from_bytes
from PIL import Image
import pytesseract

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# Load API Key
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Tesseract Path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# ---------------- TEXT EXTRACTION ----------------
def extract_text(file):
    try:
        if file.type == "application/pdf":
            try:
                with pdfplumber.open(file) as pdf:
                    text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
                    if text.strip():
                        return text
            except:
                pass

            file_bytes = file.read()
            images = convert_from_bytes(file_bytes)
            return "\n".join(pytesseract.image_to_string(img) for img in images)

        elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return docx2txt.process(file)

        elif file.type.startswith("image/"):
            image = Image.open(file)
            return pytesseract.image_to_string(image)

    except:
        return ""

    return ""


# ---------------- GEMINI ----------------
def call_gemini(text, job_description):

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

    prompt = {
        "contents": [{
            "parts": [{
                "text": f"""
Return ONLY JSON:

{{
  "name": "Candidate Name",
  "eligibility_score": number,
  "skills_score": number,
  "experience_score": number,
  "education_score": number,
  "reason": "short explanation",
  "missing_criteria": ["..."],
  "matched_skills": ["..."],
  "skill_gap_analysis": "explain missing skills",
  "suggestions": ["improvement tips"]
}}

Job Description:
{job_description[:3000]}

Resume:
{text[:7000]}
"""
            }]
        }]
    }

    try:
        res = requests.post(url, headers={"Content-Type": "application/json"}, json=prompt)
        res.raise_for_status()
        data = res.json()

        text = data["candidates"][0]["content"]["parts"][0]["text"]
        match = re.search(r'\{.*\}', text, re.DOTALL)

        return json.loads(match.group(0)) if match else None

    except Exception as e:
        st.error(f"Error: {e}")
        return None


# ---------------- PDF (RECRUITER) ----------------
def generate_pdf(results):
    path = "recruiter_report.pdf"
    doc = SimpleDocTemplate(path)
    styles = getSampleStyleSheet()

    content = []

    for r in results:
        name = r.get("name", "Candidate")

        content.append(Paragraph(f"<b>{name}</b>", styles["Title"]))
        content.append(Spacer(1, 10))

        content.append(Paragraph(f"Score: {r.get('eligibility_score', 0)}%", styles["Normal"]))
        content.append(Paragraph(f"Skills: {r.get('skills_score', 0)}", styles["Normal"]))
        content.append(Paragraph(f"Experience: {r.get('experience_score', 0)}", styles["Normal"]))
        content.append(Paragraph(f"Education: {r.get('education_score', 0)}", styles["Normal"]))

        content.append(Spacer(1, 10))

        content.append(Paragraph("<b>Strengths:</b>", styles["Normal"]))
        for s in r.get("matched_skills", []):
            content.append(Paragraph(f"- {s}", styles["Normal"]))

        content.append(Spacer(1, 10))

        content.append(Paragraph("<b>Weakness:</b>", styles["Normal"]))
        for m in r.get("missing_criteria", []):
            content.append(Paragraph(f"- {m}", styles["Normal"]))

        content.append(Spacer(1, 20))

    doc.build(content)
    return path


# ---------------- PDF (JOB SEEKER) ----------------
def generate_single_pdf(result):
    path = "job_seeker_report.pdf"
    doc = SimpleDocTemplate(path)
    styles = getSampleStyleSheet()

    content = []

    name = result.get("name", "Candidate")

    content.append(Paragraph(f"<b>{name}</b>", styles["Title"]))
    content.append(Spacer(1, 10))

    content.append(Paragraph(f"Score: {result.get('eligibility_score', 0)}%", styles["Normal"]))
    content.append(Paragraph(f"Skills: {result.get('skills_score', 0)}", styles["Normal"]))
    content.append(Paragraph(f"Experience: {result.get('experience_score', 0)}", styles["Normal"]))
    content.append(Paragraph(f"Education: {result.get('education_score', 0)}", styles["Normal"]))

    content.append(Spacer(1, 10))

    content.append(Paragraph("<b>Reason:</b>", styles["Normal"]))
    content.append(Paragraph(result.get("reason", ""), styles["Normal"]))

    content.append(Spacer(1, 10))

    content.append(Paragraph("<b>Skill Gap:</b>", styles["Normal"]))
    content.append(Paragraph(result.get("skill_gap_analysis", ""), styles["Normal"]))

    content.append(Spacer(1, 10))

    content.append(Paragraph("<b>Suggestions:</b>", styles["Normal"]))
    for s in result.get("suggestions", []):
        content.append(Paragraph(f"- {s}", styles["Normal"]))

    doc.build(content)
    return path


# ---------------- UI ----------------
st.set_page_config(page_title="AI Resume Analyzer", layout="centered")
st.title("🎯 AI Resume Analyzer")

if "mode" not in st.session_state:
    st.session_state.mode = None

if "resumes" not in st.session_state:
    st.session_state.resumes = []

if "upload_count" not in st.session_state:
    st.session_state.upload_count = 1

# Mode selection
col1, col2 = st.columns(2)

with col1:
    if st.button("👤 Job Seeker"):
        st.session_state.mode = "job"

with col2:
    if st.button("🧑‍💼 Recruiter"):
        st.session_state.mode = "rec"

# Back
if st.session_state.mode:
    if st.button("🔙 Back"):
        st.session_state.mode = None
        st.session_state.resumes = []
        st.session_state.upload_count = 1


# ---------------- JOB SEEKER ----------------
if st.session_state.mode == "job":

    file = st.file_uploader("Upload Resume", type=["pdf", "docx", "jpg", "png"])
    jd = st.text_area("Job Description")

    if file and jd:

        text = extract_text(file)
        result = call_gemini(text, jd)

        if result:
            st.metric("Score", f"{result.get('eligibility_score', 0)}%")
            st.progress(result.get("eligibility_score", 0)/100)

            st.write("Skills:", result.get("skills_score"))
            st.write("Experience:", result.get("experience_score"))
            st.write("Education:", result.get("education_score"))

            st.write("Reason:", result.get("reason"))

            st.write("📉 Skill Gap:", result.get("skill_gap_analysis"))

            st.write("💡 Suggestions")
            for s in result.get("suggestions", []):
                st.write("-", s)

            pdf = generate_single_pdf(result)

            with open(pdf, "rb") as f:
                st.download_button("📄 Download Report", f, "My_Report.pdf")


# ---------------- RECRUITER ----------------
elif st.session_state.mode == "rec":

    new_file = st.file_uploader("Upload Resume", type=["pdf", "docx"], key=f"upload_{st.session_state.upload_count}")

    if new_file:
        if new_file not in st.session_state.resumes:
            st.session_state.resumes.append(new_file)

   

    if st.session_state.resumes:
        for f in st.session_state.resumes:
            st.write("•", f.name)

    jd = st.text_area("Job Description")

    if st.button("Analyze") and jd and st.session_state.resumes:

        results = []

        for f in st.session_state.resumes:
            text = extract_text(f)
            result = call_gemini(text, jd)
            if result:
                results.append(result)

        results = sorted(results, key=lambda x: x.get("eligibility_score", 0), reverse=True)

        for r in results:
            st.write(r.get("name"))
            st.write(r.get("eligibility_score"))

        pdf = generate_pdf(results)

        with open(pdf, "rb") as f:
            st.download_button("📄 Download Report", f, "Recruiter_Report.pdf")

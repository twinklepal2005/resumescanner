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
import io

# Load .env
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Set Tesseract path (Windows)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_text(file):
    file_type = file.type
    file_name = file.name.lower()

    try:
        if file_type == "application/pdf" or file_name.endswith(".pdf"):
            try:
                with pdfplumber.open(file) as pdf:
                    text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
                    if text.strip():
                        return text
            except:
                pass
            try:
                images = convert_from_bytes(file.read())
                return "\n".join(pytesseract.image_to_string(img) for img in images)
            except:
                return ""

        elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return docx2txt.process(file)

        elif file_type.startswith("image/"):
            image = Image.open(file)
            return pytesseract.image_to_string(image)

        else:
            return ""

    except Exception as e:
        print("Text extraction error:", e)
        return ""

def call_gemini(text, job_description):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

    prompt = {
        "contents": [{
            "parts": [{
                "text": (
                    "You are a job eligibility evaluator.\n\n"
                    "Given a resume and a job description, follow these steps:\n"
                    "1. Extract name, email, phone, skills, experience, education, certifications (if any), projects, and summary from the resume.\n"
                    "2. Analyze how well the candidate matches the job description.\n"
                    "3. Return a JSON object with:\n"
                    "- 'eligibility_score' (0 to 100),\n"
                    "- 'reason' (why the score was assigned),\n"
                    "- 'missing_criteria' (any key requirements not met),\n"
                    "- 'matched_skills' (what they have that matches).\n\n"
                    "Only output a valid JSON object like:\n"
                    "{\n"
                    "  \"eligibility_score\": 85,\n"
                    "  \"reason\": \"Meets most technical skills and has 3 years relevant experience\",\n"
                    "  \"missing_criteria\": [\"AWS certification\", \"Kubernetes\"],\n"
                    "  \"matched_skills\": [\"Python\", \"Flask\", \"REST API\"]\n"
                    "}\n\n"
                    f"Job Description:\n{job_description}\n\n"
                    f"Resume:\n{text}"
                )
            }]
        }]
    }

    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, headers=headers, json=prompt)
        response.raise_for_status()
        result_text = response.json()["candidates"][0]["content"]["parts"][0]["text"]

        match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if match:
            json_str = match.group(0)
            try:
                return json.loads(json_str)
            except:
                return {"raw_output": result_text, "error": "JSON decoding failed"}
        else:
            return {"raw_output": result_text, "error": "No JSON object found"}

    except Exception as e:
        print("Gemini error:", e)
        return None

# Streamlit App UI
st.set_page_config(page_title="Resume Eligibility Scorer", layout="centered")
st.title("🎯 Resume vs Job Eligibility Scorer")

file = st.file_uploader("📄 Upload Resume (PDF, DOCX, or Image)", type=["pdf", "docx", "jpg", "jpeg", "png"])
job_description = st.text_area("📝 Paste Job Description")

if file and job_description.strip():
    with st.spinner("🔍 Extracting text from resume..."):
        resume_text = extract_text(file)

    if resume_text.strip():
        st.success("✅ Resume text extracted successfully.")
        st.text_area("📄 Extracted Resume Text (first 1500 chars)", resume_text[:1500])

        with st.spinner("🤖 Analyzing eligibility with Gemini..."):
            result = call_gemini(resume_text, job_description)

        if result:
            if "error" in result:
                st.warning("⚠️ Gemini returned a non-JSON response.")
                st.text_area("🔍 Raw Gemini Output", result["raw_output"])
            else:
                st.subheader("📌 Eligibility Report")
                score = result.get("eligibility_score", 0)

                # 🔁 Determine candidate level from score
                if score >= 80:
                    level = "Advanced"
                elif score >= 50:
                    level = "Intermediate"
                else:
                    level = "Beginner"

                st.metric("Eligibility Score", f"{score}%")
                st.metric("Candidate Level", level)
                st.write("🧠 Reason:", result.get("reason", "Not provided"))

                if "matched_skills" in result:
                    st.write("✅ Matched Skills:")
                    for skill in result["matched_skills"]:
                        st.markdown(f"- {skill}")

                if "missing_criteria" in result:
                    st.write("❌ Missing Criteria:")
                    for miss in result["missing_criteria"]:
                        st.markdown(f"- {miss}")
        else:
            st.error("❌ Gemini couldn't process the resume.")
    else:
        st.error("❌ No text could be extracted from the resume.")
elif file and not job_description.strip():
    st.warning("⚠️ Please paste the job description.")

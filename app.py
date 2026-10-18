import os
import json
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pypdf import PdfReader

load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

SYSTEM_PROMPT = """You are an expert resume reviewer and career coach.
Analyze the resume for the given target role.
Be honest, specific and practical.
The target role can be from ANY field (tech, marketing, finance, design, HR, sales, etc.).
Judge ONLY against the skills, tools and experience that this specific role really requires.
Do not assume the role is technical.
If the resume belongs to a different field than the target role, give a low score and say so in the summary.
Do not invent facts that are not in the resume.

Reply with ONLY valid JSON in exactly this format:
{
  "candidate_name": "string",
  "summary": "2-3 line profile summary",
  "ats_score": "integer from 0 to 100, match with the target role",
  "skills_found": ["string"],
  "missing_skills": ["string"],
  "strengths": ["string"],
  "weaknesses": ["string"],
  "improvements": ["string"]
}"""


def extract_text(path):
    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


def analyze(resume_text, role, jd="", retries=2):
    for attempt in range(retries + 1):
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=f"TARGET ROLE: {role}\n\nJOB DESCRIPTION (optional):\n{jd or 'Not provided'}\n\nRESUME TEXT:\n{resume_text}",
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.2,
                response_mime_type="application/json",
            ),
        )
        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            print(f"JSON kharab aaya, dobara try ({attempt + 1})...")
    raise RuntimeError("Model valid JSON nahi de paya")

st.set_page_config(page_title="Resume Analyzer", page_icon="📄")
st.title("📄 AI Resume Analyzer")

file = st.file_uploader("Resume (PDF) upload karo", type=["pdf"])
ROLES = [
    "Python Developer", "Data Analyst", "Digital Marketing Manager",
    "HR Executive", "Financial Analyst", "Graphic Designer",
    "Sales Executive", "Software Developer", "Prompt Engineer",
    "Full Stack Developer", "Others",
]

choice = st.selectbox("Target role chuno", ROLES)
if choice == "Others":
    role = st.text_input("Apna role likho", placeholder="e.g. Content Writer")
else:
    role = choice

jd = st.text_area("Job description (optional, paste karo)", height=150)

if st.button("Analyze"):
    if not file or not role:
        st.warning("Resume aur role dono chahiye.")
        st.stop()

    text = extract_text(file)
    if len(text) < 100:
        st.error("PDF se text nahi mila (scanned PDF ho sakta hai).")
        st.stop()

    with st.spinner("Analyze ho raha hai..."):
        data = analyze(text, role, jd)

    score = int(data["ats_score"])

    st.subheader(data["candidate_name"])
    st.write(data["summary"])
    st.metric("Role match score", f"{score}/100")
    st.progress(min(max(score, 0), 100) / 100)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### ✅ Skills found")
        st.write(", ".join(data["skills_found"]))
        st.markdown("### 💪 Strengths")
        for s in data["strengths"]:
            st.markdown(f"- {s}")

    with col2:
        st.markdown("### ❌ Missing skills")
        st.write(", ".join(data["missing_skills"]))
        st.markdown("### ⚠️ Weaknesses")
        for w in data["weaknesses"]:
            st.markdown(f"- {w}")

    st.markdown("### 🛠 Improvements")
    for i in data["improvements"]:
        st.markdown(f"- {i}")
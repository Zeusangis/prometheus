import os
import json
from flask import Flask, jsonify, render_template
from dotenv import load_dotenv
from flask import request as flask_request
load_dotenv()
import requests

import os
import json
import tempfile
import traceback

from flask import Flask, request, jsonify
from google import genai
from PyPDF2 import PdfReader
from dotenv import load_dotenv
from main import build_full_github_summary

load_dotenv()

app = Flask(__name__)

from gem import evaluate_transcript_json
NAVTALK_API_KEY = os.getenv("NAVTALK_API_KEY", "").strip()
NAVTALK_NAME = os.getenv("NAVTALK_NAME", "").strip()
NAVTALK_AVATAR_ID = os.getenv("NAVTALK_AVATAR_ID", "").strip()
NAVTALK_WS_BASE = os.getenv(
    "NAVTALK_WS_BASE",
    "wss://transfer.navtalk.ai/wss/v2/realtime-chat"
).strip()

CANDIDATE_NAME = "Cecil"

RESUME_JSON = {
    "personal_info": {
        "name": "Cecil Pradhan",
        "location": "Monroe, LA",
        "phone": "318-417-5517",
        "email": "cecilpradhan99@gmail.com",
        "links": {
            "linkedin": "https://linkedin.com/in/cecilpradhan1705",
            "github": "https://github.com/CecilPradhan17"
        }
    },
    "professional_summary": "Computer Science student with experience in full-stack web development, teaching, and hackathon-driven product building. Built scalable applications using React, TypeScript, Node.js, Express.js, and PostgreSQL, with experience in RAG-based AI systems, authentication, geospatial dashboards, and knowledge retrieval platforms.",
    "education": [
        {
            "institution": "University of Louisiana Monroe",
            "degree": "Bachelor of Science in Computer Science",
            "duration": "Aug 2024 - May 2028",
            "gpa": "3.9 / 4.0",
            "achievements": [
                "President's List"
            ],
            "relevant_coursework": [
                "Data Structures & Algorithms",
                "Advanced Discrete Structures",
                "Internet Programming",
                "Statistics",
                "Linear Algebra"
            ]
        }
    ],
    "technical_skills": {
        "programming_languages": [
            "JavaScript",
            "TypeScript",
            "Java",
            "Python"
        ],
        "frontend": [
            "React",
            "HTML",
            "CSS",
            "TailwindCSS"
        ],
        "backend": [
            "Node.js",
            "Express.js"
        ],
        "databases": [
            "PostgreSQL"
        ],
        "tools": [
            "Git",
            "GitHub",
            "Postman",
            "VS Code",
            "Vercel",
            "Render",
            "Neon"
        ],
        "libraries_and_apis": [
            "Google Maps API",
            "Plotly.js",
            "D3.js",
            "Chart.js"
        ]
    },
    "work_experience": [
        {
            "company": "University of Louisiana Monroe",
            "role": "Teaching Assistant",
            "location": "Monroe, LA",
            "duration": "Aug 2025 - Present",
            "responsibilities": [
                "Taught 50+ first-year students academic and technical skill development through structured instruction and mentoring.",
                "Provided weekly instructional support and mentoring, assisting with assignments and exams."
            ]
        }
    ],
    "projects": [
        {
            "name": "HawkBot",
            "tech_stack": [
                "Node.js",
                "Express.js",
                "PostgreSQL",
                "TypeScript",
                "React (Vite)",
                "TailwindCSS"
            ],
            "duration": "Jan 2026",
            "description": [
                "Built and launched a full-stack Q&A platform with discussion forum, AI chatbot, voting system, authentication, and knowledge search for 50+ active users.",
                "Generated 100+ posts within the first week of release.",
                "Implemented a RAG pipeline using OpenAI 4o-mini embeddings and cosine similarity over 1,000+ indexed knowledge prompts.",
                "Improved chatbot answer relevance by iterating on similarity thresholds using real usage data.",
                "Secured 50+ user accounts through JWT-based authentication and role-based authorization.",
                "Designed a scalable knowledge retrieval system allowing continuous ingestion of new Q&A data without retraining."
            ],
            "awards": [
                "2x 2nd Place — University Research Symposium",
                "2x 2nd Place — Honors Symposium"
            ]
        },
        {
            "name": "CarbonHorizon",
            "tech_stack": [
                "React (Vite)",
                "TypeScript",
                "TailwindCSS",
                "Google Maps API"
            ],
            "duration": "Sep 2025",
            "description": [
                "Engineered an interactive geospatial monitoring platform for 20+ Louisiana carbon capture sites.",
                "Built layered visualizations for facility locations, pipeline routes, and safety buffers.",
                "Integrated Plotly.js, D3.js, and Chart.js into dashboards surfacing live environmental data.",
                "Collaborated in a 4-person team to architect, build, and deploy the platform within a hackathon timeframe."
            ],
            "awards": [
                "1st Place — Nexus ClimateTech DevDays ($5,000 Award)"
            ]
        },
        {
            "name": "DonorSync",
            "tech_stack": [
                "JavaScript",
                "HTML",
                "CSS"
            ],
            "duration": "Jul 2025",
            "description": [
                "Designed a location-based matching system connecting hospitals with nearby donors across 10+ simulated donor records.",
                "Built modular frontend components with structured local data handling.",
                "Improved registration and request workflows for efficient donor management."
            ],
            "awards": [
                "Hackathon Finalist — 1 of 10 selected from 80+ applicants in the Nexus Louisiana Technology Cup"
            ]
        }
    ],
    "leadership_and_activities": [
        "CodePath (Technical Interview Prep course over the summer)",
        "Google Developers Student Club (Active member, participated in 8+ workshops)",
        "ULM Honors Program (Organized 10+ events)",
        "Student Government Association"
    ]
}

PROJECT_JSON = {
    "behavioral_areas": [
        "teamwork",
        "ownership",
        "conflict resolution",
        "learning from mistakes",
        "handling ambiguity",
        "communication"
    ],
    "priority_topics": [
        "HawkBot",
        "CarbonHorizon",
        "DonorSync",
        "Teaching Assistant experience",
        "Hackathon teamwork",
        "RAG pipeline implementation",
        "Authentication and authorization design",
        "Geospatial dashboard development"
    ]
}

def build_interview_prompt():
    return f"""
# Role & Objective
You are Lauren, a professional technical interviewer from Prometheus.

You are interviewing {CANDIDATE_NAME} for a Software Engineer Intern role.

Your job is to conduct a SHORT, NATURAL, HUMAN-LIKE interview.

# Personality & Tone
- Warm
- Professional
- Conversational
- Calm
- Concise
- Slightly challenging but friendly
- Your speaking style should match a professional female interviewer persona named Lauren

# Duration
- HARD MAXIMUM: 3 minutes total
- Ask only 4 to 5 main questions total
- Keep the interview moving quickly

# Critical Interview Behavior
- START THE CONVERSATION YOURSELF
- Greet the candidate by name
- Use the candidate's name naturally at the beginning of each new question
- Sound like a real interviewer, not a chatbot
- Ask ONE question at a time
- WAIT for the answer before asking the next question
- Ask AT MOST one short follow-up on a topic, and only if needed
- After one follow-up, MOVE ON
- DO NOT stay too long on the same project
- DO NOT ask for too many technical details about every project
- Mix technical and behavioral questions
- Cover both project/work experience and behavioral/situational topics
- Prefer breadth over excessive depth because the interview is short
- Use brief acknowledgments naturally, like "Got it" or "Thanks, {CANDIDATE_NAME}"
- Do not sound repetitive

# Question Mix
Use a balanced flow:
1. Opening introduction
2. One project question
3. One work-experience or technical reasoning question
4. One behavioral or situational question
5. One short closing question if time allows

# Topic Switching Rules
- After discussing a project and one follow-up maximum, switch topics
- Do not ask multiple deep-detail questions on the same project
- If the candidate gives a solid answer, do not keep digging
- Move naturally from projects to experience to behavioral questions

# Behavioral Questions
Include at least one strong behavioral or situational question such as:
- Tell me about a time you faced a challenge while working with others
- Tell me about a time you had to learn something quickly
- Tell me about a time you handled ambiguity or solved a problem with limited guidance
- Tell me about a time you made a mistake and what you learned

# Opening
Your first spoken line must be exactly:
"Hello {CANDIDATE_NAME}, I'm Lauren from Prometheus. Thanks for joining today. To start, could you briefly introduce yourself and share one project you're most proud of?"

# Question Addressing Rule
For each NEW question after the first, begin with the candidate name naturally, like:
- "{CANDIDATE_NAME}, can you tell me..."
- "{CANDIDATE_NAME}, I'd like to hear about..."
- "{CANDIDATE_NAME}, walk me through..."

# Ending
When time is nearly over, end warmly and professionally with something close to:
"Thank you, {CANDIDATE_NAME}. That covers everything I wanted to ask today. It was great speaking with you."

# Candidate Resume JSON
{json.dumps(RESUME_JSON, indent=2)}

# Project / Interview Context JSON
{json.dumps(PROJECT_JSON, indent=2)}
""".strip()


INTERVIEWER_CONFIG = {
    "company": "Prometheus",
    "role": "Software Engineer Intern",
    "voice": "shimmer",
    "candidateName": CANDIDATE_NAME,
    "durationMs": 3 * 60 * 1000,
    "wrapUpMs": 2 * 60 * 1000,
    "openingLine": f"Hello {CANDIDATE_NAME}, I'm Lauren from Prometheus. Thanks for joining today. To start, could you briefly introduce yourself and share one project you're most proud of?",
    "systemPrompt": build_interview_prompt()
}


@app.route("/transcript", methods=["POST"])
def transcript():
    data = flask_request.get_json(force=True)
    print("Received transcript:")
    print(data.get("transcriptText", ""))

    # save to db / file here if you want
    evaluation_result = evaluate_transcript_json(data.get("transcriptText", ""))
    return jsonify(evaluation_result)

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/session")
def api_session():
    if not NAVTALK_API_KEY:
        return jsonify({
            "success": False,
            "error": "Missing NAVTALK_API_KEY in .env"
        }), 500

    if not NAVTALK_NAME and not NAVTALK_AVATAR_ID:
        return jsonify({
            "success": False,
            "error": "Set NAVTALK_NAME or NAVTALK_AVATAR_ID in .env"
        }), 500

    return jsonify({
        "success": True,
        "apiKey": NAVTALK_API_KEY,
        "wsBase": NAVTALK_WS_BASE,
        "name": NAVTALK_NAME or None,
        "avatarId": NAVTALK_AVATAR_ID or None,
        "interviewer": INTERVIEWER_CONFIG
    })


@app.route("/api/health")
def api_health():
    return jsonify({"success": True, "message": "Flask backend is running"})






API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise ValueError("Missing Gemini API key. Set GEMINI_API_KEY or GOOGLE_API_KEY.")

client = genai.Client(api_key=API_KEY)


def extract_pdf_text(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    return "\n".join(page.extract_text() or "" for page in reader.pages).strip()


def build_prompt(text: str) -> str:
    return f"""
You are an ATS (Applicant Tracking System) evaluator.

Your task is to analyze a resume and return a detailed ATS score.

### INPUT:
RESUME:
{text}

### INSTRUCTIONS:
1. Evaluate the resume based on these categories:
- Keyword Match (0–25)
- Skills Alignment (0–15)
- Experience Relevance (0–20)
- Education & Certifications (0–10)
- Formatting & ATS Readability (0–10)
- Achievements & Impact (0–10)
- Section Completeness (0–10)

2. Calculate TOTAL SCORE out of 100.

3. Identify:
- Missing keywords
- Weak bullet points
- Formatting issues

4. Provide:
- Top 5 improvements with highest impact
- Rewritten bullet points if possible
- Suggested keywords to add naturally

Also at the end, list the projects mentioned in the resume.

Return only valid JSON matching the schema.
""".strip()



def analyze_resume(text: str):
    schema = {
        "type": "object",
        "properties": {
            "ats_score": {"type": "integer"},
            "breakdown": {
                "type": "object",
                "properties": {
                    "keyword_match": {"type": "integer"},
                    "skills_alignment": {"type": "integer"},
                    "experience_relevance": {"type": "integer"},
                    "education": {"type": "integer"},
                    "formatting": {"type": "integer"},
                    "achievements": {"type": "integer"},
                    "completeness": {"type": "integer"}
                },
                "required": [
                    "keyword_match",
                    "skills_alignment",
                    "experience_relevance",
                    "education",
                    "formatting",
                    "achievements",
                    "completeness"
                ]
            },
            "missing_keywords": {"type": "array", "items": {"type": "string"}},
            "weak_areas": {"type": "array", "items": {"type": "string"}},
            "top_improvements": {"type": "array", "items": {"type": "string"}},
            "projects": {"type": "array", "items": {"type": "string"}},
            "final_verdict": {"type": "string"}
        },
        
        "required": [
            "ats_score",
            "breakdown",
            "missing_keywords",
            "weak_areas",
            "top_improvements",
            "projects",
            "final_verdict"
        ]
    }

    prompt = build_prompt(text)

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_json_schema": schema
        }
    )

    return json.loads(response.text)


@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Server running"}), 200


@app.route("/test-gemini", methods=["GET"])
def test_gemini():
    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents="Reply with OK"
        )
        return jsonify({
            "success": True,
            "text": response.text
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "trace": traceback.format_exc()
        }), 500


@app.route("/analyze-resume", methods=["POST"])
def analyze_resume_api():
    temp_pdf_path = None

    try:
        if "resume" not in request.files:
            return jsonify({"error": "No resume file uploaded. Use key 'resume'."}), 400

        file = request.files["resume"]

        if file.filename == "":
            return jsonify({"error": "Empty filename."}), 400

        if not file.filename.lower().endswith(".pdf"):
            return jsonify({"error": "Only PDF files are supported."}), 400

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            file.save(temp_file.name)
            temp_pdf_path = temp_file.name

        text = extract_pdf_text(temp_pdf_path)
        if not text:
            return jsonify({"error": "Could not extract text from PDF."}), 400

        result = analyze_resume(text)
        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            "error": str(e),
            "error_type": type(e).__name__,
            "trace": traceback.format_exc()
        }), 500

    finally:
        if temp_pdf_path and os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)


@app.route("/analyze-github/<username>/<project1>/<project2>", methods=["GET"])
def analyze_github_api(username, project1, project2):
    try:
        projects = [project1, project2]

        if not username:
            return jsonify({"error": "username is required"}), 400

        if not isinstance(projects, list):
            return jsonify({"error": "projects must be a list"}), 400

        summary = build_full_github_summary(
            username=username,
            
            projects=projects,
            github_token=os.getenv("github_token") ,
            gemini_api_key=os.getenv("GEMINI_API_KEY") ,
            repo_workers=8,
            gemini_model="gemini-2.5-flash-lite"
        )

        return jsonify(summary)

    except Exception as e:
        return jsonify({
            "error": str(e),
            "error_type": type(e).__name__,
            "trace": traceback.format_exc()
        }), 500



from flask import Flask, render_template, request, redirect, url_for
base_url = "http://localhost:5000"  





from urllib.parse import quote
from flask import render_template, request
import requests

@app.route("/portfolio-review", methods=["GET"])
def portfolio_review():
    return render_template("form.html")


@app.route("/portfolio-review/result", methods=["POST"])
def portfolio_review_result():
    try:
        resume = request.files.get("resume")
        username = request.form.get("username", "").strip()
        project1 = request.form.get("project1", "").strip()
        project2 = request.form.get("project2", "").strip()

        if not resume:
            return "Resume file is required", 400

        if not username or not project1 or not project2:
            return "Username and two favorite projects are required", 400

        base_url = request.host_url.rstrip("/")

        resume_response = requests.post(
            f"{base_url}/analyze-resume",
            files={
                "resume": (
                    resume.filename,
                    resume.stream,
                    resume.mimetype or "application/pdf"
                )
            },
            timeout=180
        )

        if resume_response.status_code != 200:
            return f"Resume analysis failed: {resume_response.text}", 500

        resume_data = resume_response.json()

        github_response = requests.get(
            f"{base_url}/analyze-github/{quote(username)}/{quote(project1)}/{quote(project2)}",
            timeout=180
        )

        if github_response.status_code != 200:
            return f"GitHub analysis failed: {github_response.text}", 500

        github_data = github_response.json()

        return render_template(
            "dashboard.html",
            resume_data=resume_data,
            github_data=github_data,
            username=username,
            project1=project1,
            project2=project2
        )

    except Exception as e:
        return f"Something went wrong: {str(e)}", 500




if __name__ == "__main__":
    app.run(debug=True)


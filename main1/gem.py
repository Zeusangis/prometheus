import os
import json
from dotenv import load_dotenv
from google import genai

load_dotenv()

# ✅ Initialize client ONCE
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# ✅ JSON Schema
schema = {
    "type": "object",
    "properties": {
        "overall_recommendation": {
            "type": "string",
            "enum": ["Strong Hire", "Hire", "Lean Hire", "Lean Reject", "Reject"]
        },
        "scores": {
            "type": "object",
            "properties": {
                "communication_clarity": {"type": "integer", "minimum": 0, "maximum": 10},
                "natural_delivery": {"type": "integer", "minimum": 0, "maximum": 10},
                "thought_process": {"type": "integer", "minimum": 0, "maximum": 10},
                "creativity": {"type": "integer", "minimum": 0, "maximum": 10},
                "technical_depth": {"type": "integer", "minimum": 0, "maximum": 10},
                "explainability": {"type": "integer", "minimum": 0, "maximum": 10},
                "pause_handling": {"type": "integer", "minimum": 0, "maximum": 10},
                "confidence": {"type": "integer", "minimum": 0, "maximum": 10},
                "focus_relevance": {"type": "integer", "minimum": 0, "maximum": 10}
            },
            "required": [
                "communication_clarity",
                "natural_delivery",
                "thought_process",
                "creativity",
                "technical_depth",
                "explainability",
                "pause_handling",
                "confidence",
                "focus_relevance"
            ]
        },
        "strengths": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1
        },
        "weaknesses": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1
        }
    },
    "required": ["overall_recommendation", "scores", "strengths", "weaknesses"]
}

# ✅ Clean Prompt (NO .format issues)
BASE_PROMPT = """
You are a local company HR evaluating a candidate for an internship.

Be fair and easy to 


Scoring:
0–3 poor | 4–5 below | 6–7 acceptable | 8 strong | 9+ exceptional

Return ONLY valid JSON in this format:

{
  "overall_recommendation": "Strong Hire | Hire | Lean Hire | Lean Reject | Reject",
  "scores": {
    "communication_clarity": int,
    "natural_delivery": int,
    "thought_process": int,
    "creativity": int,
    "technical_depth": int,
    "explainability": int,
    "pause_handling": int,
    "confidence": int,
    "focus_relevance": int
  },
  "strengths": ["...", "..."],
  "weaknesses": ["...", "..."]
}
"""

# ✅ Main function
def evaluate_transcript_json(transcript: str):
    prompt = f"{BASE_PROMPT}\n\nTranscript:\n{transcript}"

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",  # stable model
            contents=prompt,
            config={
                "temperature": 0.3,  # balanced
                "response_mime_type": "application/json",
                "response_json_schema": schema
            }
        )

        return json.loads(response.text)

    except Exception as e:
        return {"error": str(e)}




sample_text="""Prometheus
11:28 PM
Hello Cecil, I'm Lauren from Prometheus. Thanks for joining today. To start, could you briefly introduce yourself and share one project you're most proud of?
You
11:28 PM
Hello.
You
11:29 PM
My name is Tesla Pradhan, and I am a sophomore computer science major at the University of Louisiana Monroe. I am interested in full-stack software development. I have worked on multiple projects, the latest one being a college chatbot called Hawkbot, which answers the students' questions.
You
11:29 PM
and finds...
You
11:29 PM
The answer's if it can't.
You
11:29 PM
Find it in the database.
Prometheus
11:29 PM
Thanks for sharing that, Cecil. It sounds like HawkBot was a significant project. Now, Cecil, can you tell me what technologies you used on that project and why you chose them?
You
11:29 PM
So for the front-end, I used React, Vite, Tailwind, and TypeScript because it requires a very
Prometheus
11:29 PM
Got it. Cecil, why did you choose React and TypeScript—was it specific to
You
11:29 PM
interactive and dynamic.
You
11:29 PM
Frontend, whereas for the backend, I used Node, Express, and Postgres database because it would, it allows the
You
11:29 PM
Um...
You
11:30 PM
integration to be very seamless, and the data for Postgres requires a lot of relationships between them.
Prometheus
11:30 PM
That makes sense. Thanks for explaining that, Cecil. Now, let’s switch gears. Can you tell me about a time you faced a challenge while working with others?
You
11:30 PM
Não.
Prometheus
11:30 PM
That's okay, Cecil. Could you describe a time when you had to learn something quickly—what was the situation and how did you manage it?
You
11:30 PM
Não.
Prometheus
11:30 PM
That's fine, Cecil. Let's try this: Can you tell me about a time you handled some ambiguity on a project, how you approached it, and what the outcome was?
You
11:30 PM
No.
Prometheus
11:30 PM
Thanks for letting me know. Let's take a different approach. Cecil, can you share one key lesson you've learned from your teaching assistant experience? That would be helpful.
You
11:31 PM
As a teaching assistant,
You
11:31 PM
I've improved my public speaking ability, my organizational skills, my management skills, and leadership ability.
Prometheus
11:31 PM
That’s great to hear, Cecil. Improving those skills is really valuable. Thank you for sharing. That covers everything I wanted to ask today. It was great speaking with you."""

# data=evaluate_transcript_json(sample_text)
# print(data)
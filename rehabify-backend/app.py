from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from google import genai
import json

app = FastAPI()

app.add_middleware(
CORSMiddleware,
allow_origins=["*"],
allow_methods=["*"],
allow_headers=["*"]
)

client = genai.Client(
api_key="AQ.Ab8RN6LDZAuLtA4yPE09io9mYsgEC7uejl8YuLdMz-nP0GvQsg"
)

@app.get("/session-report")
def session_report():
    try:
        with open(
            r"C:\Users\SATHYA\rehab-web\session_report.json",
            "r"
        ) as f:
            data = json.load(f)

            print("REPORT FOUND")
            print(data)

            return data

    except Exception as e:
        print("SESSION REPORT ERROR")
        print(e)

        return {
            "max_angle": 0,
            "reps": 0,
            "posture_score": 0,
            "score": 0,
            "duration": 0
        }

@app.post("/generate-profile")
async def generate_profile(data: dict):
    prompt = f"""
You are an AI physiotherapy assistant.

Patient Assessment:

{json.dumps(data, indent=2)}

Analyze the assessment and generate a realistic recovery profile.

Return ONLY valid JSON.

Example:

{{
"diagnosis": "Shoulder Mobility Restriction",
"phase": "Mobility Recovery",
"timeline": "6-8 Weeks",
"focus": "Improve shoulder mobility and reduce pain during overhead movement."
}}

Generate values based on the assessment data.
Do not leave fields empty.
Do not use markdown.
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        text = response.text.strip()

        text = text.replace("```json", "")
        text = text.replace("```", "")

        try:
            return json.loads(text)

        except Exception:
            return {
                "diagnosis": "Recovery Program",
                "phase": "Foundation",
                "timeline": "4-8 Weeks",
                "focus": text
            }

    except Exception as e:
        print("GEMINI ERROR")
        print(e)

        return {
            "diagnosis": "Shoulder Mobility Restriction",
            "phase": "Mobility Recovery",
            "timeline": "6-8 Weeks",
            "focus": "Gemini quota exceeded. Using fallback recovery profile."
        }

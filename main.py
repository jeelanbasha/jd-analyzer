from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from anthropic import Anthropic
import json
import re

load_dotenv()

app = FastAPI(title="JD Analyzer API")
client = Anthropic()

class JDRequest(BaseModel):
    jd_text: str

class MatchRequest(BaseModel):
    jd_text: str
    resume_text: str

@app.get("/health")
def health():
    return {"status": "ok", "model": "claude-sonnet-4-5"}

def clean_text(text: str) -> str:
    # normalize whitespace and remove problematic characters
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)  # remove non-ASCII
    text = re.sub(r'\n{3,}', '\n\n', text)        # max 2 consecutive newlines
    return text.strip()

@app.post("/analyze-jd")
def analyze_jd(request: JDRequest):
    jd_text = clean_text(request.jd_text)
    if not jd_text.strip():
        raise HTTPException(status_code=400, detail="jd_text cannot be empty")
    
    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": f"""Analyze this job description and extract information.
Return ONLY raw JSON. No markdown. No backticks. No explanation.
Just the JSON object starting with {{ and ending with }}. Use these exact keys:
- required_skills (list of strings)
- nice_to_have (list of strings)
- years_experience (string)
- level (junior/mid/senior)
- red_flags (list of strings)

Job description:
{jd_text}"""
        }]
    )
    
    try:
        result = json.loads(message.content[0].text)
    except json.JSONDecodeError:
        result = {"raw": message.content[0].text}
    
    return {
        "result": result,
        "usage": {
            "input_tokens": message.usage.input_tokens,
            "output_tokens": message.usage.output_tokens
        }
    }

@app.post("/match-resume")
def match_resume(request: MatchRequest):
    jd_text = clean_text(request.jd_text)        # add this
    resume_text = clean_text(request.resume_text)  # add this
    
    if not jd_text.strip() or not resume_text.strip():
        raise HTTPException(status_code=400, detail="Both fields required")
    
    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": f"""Compare this resume against the job description.
Return ONLY raw JSON. No markdown. No backticks. No explanation.
Just the JSON object starting with {{ and ending with }}. Use these exact keys:
- match_score (integer 0-100)
- matched_skills (list of strings)
- missing_skills (list of strings)
- recommendation (one sentence string)

Job description:
{jd_text}

Resume:
{resume_text}"""        # change request.resume_text to resume_text
        }]
    )
    
    try:
        result = json.loads(message.content[0].text)
    except json.JSONDecodeError:
        result = {"raw": message.content[0].text}
    
    return {
        "result": result,
        "usage": {
            "input_tokens": message.usage.input_tokens,
            "output_tokens": message.usage.output_tokens
        }
    }
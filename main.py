from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from anthropic import Anthropic
import json
import re

load_dotenv()

app = FastAPI(title="JD Analyzer API")
client = Anthropic()

def clean_text(text: str) -> str:
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def parse_body(raw: bytes) -> dict:
    text = raw.decode("utf-8")
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    return json.loads(text)

@app.get("/health")
def health():
    return {"status": "ok", "model": "claude-sonnet-4-5"}

@app.post("/analyze-jd")
async def analyze_jd(request: Request):
    try:
        body = parse_body(await request.body())
        jd_text = clean_text(body.get("jd_text", ""))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")
    
    if not jd_text:
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
async def match_resume(request: Request):
    try:
        body = parse_body(await request.body())
        jd_text = clean_text(body.get("jd_text", ""))
        resume_text = clean_text(body.get("resume_text", ""))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")
    
    if not jd_text or not resume_text:
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
{resume_text}"""
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
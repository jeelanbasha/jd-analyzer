from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from anthropic import Anthropic
from app.mentor_agent import run_mentor_agent
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.gap_analyzer import analyze_resume_gap
import json
import re
import uuid
import asyncio


load_dotenv()

app = FastAPI(title="JD Analyzer API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
def serve_frontend():
    return FileResponse("frontend/index.html")
client = Anthropic()

# keep these for Swagger UI documentation
class JDRequest(BaseModel):
    jd_text: str

class MatchRequest(BaseModel):
    jd_text: str
    resume_text: str

class MentorRequest(BaseModel):
    roles: list[str]
    location: str
    resume_text: Optional[str] = ""

@app.post("/mentor/analyze-market")
async def analyze_market(request: Request):
    try:
        body = parse_body(await request.body())
        roles = body.get("roles", ["AI Engineer"])
        location = body.get("location", "New York")
        resume_text = body.get("resume_text", "")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")

    if not roles or not location:
        raise HTTPException(status_code=400, detail="roles and location are required")

    try:
        result = await run_mentor_agent(
            roles=roles,
            location=location,
            resume_text=resume_text
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mentor agent failed: {str(e)}")

def clean_text(text: str) -> str:
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def parse_body(raw: bytes) -> dict:
    # decode
    text = raw.decode("utf-8", errors="ignore")
    
    # strip ALL control characters except tab, newline, carriage return
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    
    # now find the jd_text value and clean inside it
    # replace literal newlines inside JSON string values with \n escape
    def clean_json_string(match):
        content = match.group(1)
        content = content.replace('\n', '\\n')
        content = content.replace('\r', '\\r')
        content = content.replace('\t', '\\t')
        return f'"{content}"'
    
    # apply to all string values in the JSON
    text = re.sub(r'"((?:[^"\\]|\\.)*)"', clean_json_string, text)
    
    return json.loads(text)

@app.get("/health")
def health():
    return {"status": "ok", "model": "claude-sonnet-4-5"}

@app.post("/analyze-jd", response_model=None, openapi_extra={
    "requestBody": {
        "content": {
            "application/json": {
                "schema": JDRequest.model_json_schema()
            }
        }
    }
})
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
- required_skills (list of strings — use full names not abbreviations, e.g. "quality assurance" not "QA", "machine learning" not "ML", "product management" not "PM", "continuous integration" not "CI/CD")
- nice_to_have (list of strings — normalized full names)
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

@app.post("/match-resume", response_model=None, openapi_extra={
    "requestBody": {
        "content": {
            "application/json": {
                "schema": MatchRequest.model_json_schema()
            }
        }
    }
})
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

# in-memory job store
jobs = {}

@app.post("/mentor/start")
async def start_mentor(request: Request):
    try:
        body = parse_body(await request.body())
        roles = body.get("roles", ["AI Engineer"])
        location = body.get("location", "New York")
        resume_text = body.get("resume_text", "")
        experience_level = body.get("experience_level", "")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")

    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {"status": "running", "result": None}

    async def run():
        try:
            result = await run_mentor_agent(
                roles=roles,
                location=location,
                resume_text=resume_text,
                experience_level=experience_level
            )
            jobs[job_id] = {"status": "done", "result": result}
        except Exception as e:
            jobs[job_id] = {"status": "error", "error": str(e)}

    asyncio.create_task(run())
    return {"job_id": job_id, "status": "running", "message": "Job started."}

@app.get("/mentor/status/{job_id}")
def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]
@app.post("/mentor/gap-analysis")
async def gap_analysis(request: Request):
    try:
        body = parse_body(await request.body())
        resume_text = body.get("resume_text", "")
        market_report = body.get("market_report", {})
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")

    if not resume_text:
        raise HTTPException(status_code=400, detail="resume_text is required")

    if not market_report:
        raise HTTPException(status_code=400, detail="market_report is required")

    result = analyze_resume_gap(resume_text, market_report)
    return result
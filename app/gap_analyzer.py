import os
import json
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()

def analyze_resume_gap(
    resume_text: str,
    market_report: dict
) -> dict:
    top_skills = market_report.get("top_required_skills", [])
    nice_to_have = market_report.get("top_nice_to_have", [])

    skills_data = json.dumps({
        "required_skills": top_skills[:15],
        "nice_to_have": nice_to_have[:10]
    }, indent=2)

    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2048,
        messages=[{
            "role": "user",
            "content": f"""You are a senior hiring manager with expertise across software engineering, AI, embedded systems, and technology roles.
Analyze this resume against the market skill requirements for the roles being targeted and return a gap analysis.

RESUME:
{resume_text}

MARKET SKILL DATA (from {market_report.get('total_jobs_analyzed', 0)} real job postings):
{skills_data}

Return ONLY raw JSON. No markdown. No backticks. No explanation. Start your response with {{ and end with }}. Use these exact keys:
{{
  "confirmed_skills": [
    {{"skill": "skill name", "evidence": "where in resume", "strength": "strong/moderate/basic"}}
  ],
  "gap_skills": [
    {{"skill": "skill name", "market_frequency": 0, "priority": "critical/high/medium", "learn_in_days": 0, "resource": "specific resource to learn this"}}
  ],
  "match_score": 0,
  "summary": "2 sentence honest assessment",
  "learning_plan": [
    {{"week": 1, "focus": "what to learn", "outcome": "what you can do after"}}
  ],
  "strengths": ["strength 1", "strength 2"],
  "quick_wins": ["thing you can add to resume now without learning anything new"]
}}

Be brutally honest. Base gap_skills priority on market_frequency percentage.
For learn_in_days be realistic. For resources be specific (exact course name, doc URL, not just 'read docs')."""
        }]
    )

    try:
        text = message.content[0].text.strip()
        # aggressively strip all markdown formatting
        if "```" in text:
            # extract content between first ``` and last ```
            parts = text.split("```")
            # parts[1] contains the json (possibly with 'json' prefix)
            if len(parts) >= 2:
                text = parts[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()
        return json.loads(text)
    except (json.JSONDecodeError, IndexError):
        # last resort — try to find JSON object in the text
        try:
            start = message.content[0].text.find("{")
            end = message.content[0].text.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(message.content[0].text[start:end])
        except json.JSONDecodeError:
            pass
        return {"raw": message.content[0].text}
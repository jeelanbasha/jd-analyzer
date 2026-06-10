import os
from dotenv import load_dotenv  # add this
from anthropic import Anthropic

load_dotenv()  # add this — reads your .env file

client = Anthropic()

def analyze_job_description(jd_text: str) -> dict:
    """
    Takes a job description and extracts key information using Claude.
    """
    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""Analyze this job description and extract:
1. Required skills (list)
2. Nice-to-have skills (list)
3. Years of experience required
4. Experience level (junior/mid/senior)
5. Any red flags

Job description:
{jd_text}

Return as a structured format."""
            }
        ]
    )
    
    return {
        "raw_response": message.content[0].text,
        "usage": {
            "input_tokens": message.usage.input_tokens,
            "output_tokens": message.usage.output_tokens
        }
    }

if __name__ == "__main__":
    # Test with a sample JD
    sample_jd = """
    Senior Python Engineer
    5+ years of Python experience required
    Experience with FastAPI, async/await, PostgreSQL
    Nice to have: Kubernetes, Docker, Redis
    """
    
    result = analyze_job_description(sample_jd)
    print(result["raw_response"])
    print(f"\nTokens used: {result['usage']}")
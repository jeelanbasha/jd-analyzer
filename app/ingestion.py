import os
import httpx
import asyncio
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional

load_dotenv()

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")
ADZUNA_BASE_URL = "https://api.adzuna.com/v1/api/jobs/us/search"

class JobPosting(BaseModel):
    id: str
    title: str
    company: str
    location: str
    description: str
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    url: str
    created: Optional[str] = None

def parse_job(raw: dict) -> JobPosting:
    return JobPosting(
        id=raw.get("id", ""),
        title=raw.get("title", ""),
        company=raw.get("company", {}).get("display_name", "Unknown"),
        location=raw.get("location", {}).get("display_name", "Unknown"),
        description=raw.get("description", ""),
        salary_min=raw.get("salary_min"),
        salary_max=raw.get("salary_max"),
        url=raw.get("redirect_url", "")
        created=raw.get("created", "")
    )

async def fetch_jobs(
    role: str,
    location: str = "United States",
    count: int = 20,
    experience_level: str = ""
) -> list[JobPosting]:
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "what": role,
        "where": location,
        "results_per_page": count,
        "content-type": "application/json"
    }

    # map our levels to Adzuna's expected experience ranges
    exp_map = {
        "junior": "1",
        "mid": "3",
        "senior": "6"
    }
    if experience_level and experience_level in exp_map:
        params["experience"] = exp_map[experience_level]

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{ADZUNA_BASE_URL}/1",
            params=params,
            timeout=10.0
        )
        response.raise_for_status()
        data = response.json()

    jobs = [parse_job(job) for job in data.get("results", [])]
    print(f"Fetched {len(jobs)} jobs for '{role}' in '{location}'")
    return jobs

async def fetch_multiple_roles(
    roles: list[str],
    location: str = "United States",
    experience_level: str = ""
) -> list[JobPosting]:
    tasks = [fetch_jobs(role, location, experience_level=experience_level) for role in roles]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_jobs = []
    for role, result in zip(roles, results):
        if isinstance(result, Exception):
            print(f"Failed to fetch '{role}': {result}")
        else:
            all_jobs.extend(result)

    seen_ids = set()
    unique_jobs = []
    for job in all_jobs:
        if job.id not in seen_ids:
            seen_ids.add(job.id)
            unique_jobs.append(job)

    print(f"Total unique jobs: {len(unique_jobs)}")
    return unique_jobs

if __name__ == "__main__":
    async def main():
        jobs = await fetch_multiple_roles(
            roles=["AI Engineer", "Machine Learning Engineer", "LLM Engineer"],
            location="New York"
        )
        for job in jobs[:3]:
            print(f"\n{job.title} @ {job.company}")
            print(f"Location: {job.location}")
            print(f"URL: {job.url}")
            print(f"Description preview: {job.description[:200]}...")

    asyncio.run(main())
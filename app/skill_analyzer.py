import asyncio
import json
import httpx
from collections import Counter
from app.ingestion import JobPosting
from typing import Optional

ANALYZER_URL = "http://localhost:8000/analyze-jd"

async def analyze_single_job(
    client: httpx.AsyncClient,
    job: JobPosting
) -> Optional[dict]:
    try:
        response = await client.post(
            ANALYZER_URL,
            json={"jd_text": job.description},
            timeout=30.0
        )
        response.raise_for_status()
        data = response.json()
        result = data.get("result", {})

        if "raw" in result:
            return None

        return {
            "job_id": job.id,
            "title": job.title,
            "company": job.company,
            "required_skills": result.get("required_skills", []),
            "nice_to_have": result.get("nice_to_have", []),
            "level": result.get("level", "unknown"),
            "years_experience": result.get("years_experience", "unknown"),
            "red_flags": result.get("red_flags", [])
        }
    except Exception as e:
        print(f"Failed to analyze {job.title} @ {job.company}: {e}")
        return None

async def analyze_jobs_batch(
    jobs: list[JobPosting],
    batch_size: int = 5
) -> list[dict]:
    results = []

    for i in range(0, len(jobs), batch_size):
        batch = jobs[i:i + batch_size]
        print(f"Analyzing batch {i//batch_size + 1} of {len(jobs)//batch_size + 1}...")

        async with httpx.AsyncClient() as client:
            tasks = [analyze_single_job(client, job) for job in batch]
            batch_results = await asyncio.gather(*tasks)

        valid = [r for r in batch_results if r is not None]
        results.extend(valid)
        print(f"Batch complete: {len(valid)}/{len(batch)} succeeded")

        await asyncio.sleep(1)

    return results

def compute_skill_frequency(analyses: list[dict]) -> dict:
    required_counter = Counter()
    nice_counter = Counter()
    level_counter = Counter()

    for analysis in analyses:
        for skill in analysis.get("required_skills", []):
            required_counter[skill.lower().strip()] += 1
        for skill in analysis.get("nice_to_have", []):
            nice_counter[skill.lower().strip()] += 1
        level_counter[analysis.get("level", "unknown")] += 1

    total = len(analyses)

    return {
        "total_jobs_analyzed": total,
        "top_required_skills": [
            {"skill": skill, "count": count, "percentage": round(count/total*100)}
            for skill, count in required_counter.most_common(15)
        ],
        "top_nice_to_have": [
            {"skill": skill, "count": count, "percentage": round(count/total*100)}
            for skill, count in nice_counter.most_common(10)
        ],
        "level_distribution": dict(level_counter)
    }

def print_market_report(report: dict) -> None:
    print("\n" + "="*50)
    print("MARKET SKILL REPORT")
    print("="*50)
    print(f"Jobs analyzed: {report['total_jobs_analyzed']}")

    print("\nTOP REQUIRED SKILLS:")
    for item in report["top_required_skills"]:
        bar = "█" * (item["percentage"] // 5)
        print(f"  {item['skill']:<30} {bar} {item['percentage']}%")

    print("\nTOP NICE TO HAVE:")
    for item in report["top_nice_to_have"]:
        print(f"  {item['skill']:<30} {item['count']} jobs")

    print("\nROLE LEVELS:")
    for level, count in report["level_distribution"].items():
        print(f"  {level:<15} {count} jobs")

if __name__ == "__main__":
    async def main():
        from app.ingestion import fetch_multiple_roles

        print("Fetching jobs...")
        jobs = await fetch_multiple_roles(
            roles=["AI Engineer", "Machine Learning Engineer", "LLM Engineer"],
            location="New York"
        )

        print(f"\nAnalyzing {len(jobs)} jobs with Claude...")
        print("Make sure your FastAPI server is running: uvicorn app.main:app --reload")
        print()

        analyses = await analyze_jobs_batch(jobs, batch_size=5)

        report = compute_skill_frequency(analyses)
        print_market_report(report)

        with open("data/skill_report.json", "w") as f:
            json.dump({"report": report, "analyses": analyses}, f, indent=2)
        print("\nFull report saved to data/skill_report.json")

    asyncio.run(main())
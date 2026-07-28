import asyncio
from app.ingestion import fetch_multiple_roles, JobPosting
from app.vector_store import store_jobs, query_jobs, collection_count
from app.skill_analyzer import analyze_jobs_batch, compute_skill_frequency

async def run_mentor_agent(
    roles: list[str],
    location: str,
    resume_text: str = "",
    experience_level: str = ""
) -> dict:
    jobs = await fetch_multiple_roles(roles=roles, location=location)

    if not jobs:
        return {"error": "No jobs found for given roles and location"}

    store_jobs(jobs)
    analyses = await analyze_jobs_batch(jobs, batch_size=5)

    # filter by experience level after Claude extracts it
    if experience_level and experience_level != "":
        analyses = [a for a in analyses if a.get("level", "").lower() == experience_level.lower()]
        if not analyses:
            analyses = await analyze_jobs_batch(jobs, batch_size=5)  # fallback to all if filter too strict

    report = compute_skill_frequency(analyses)

    similar_jobs = []
    if resume_text.strip():
        print(f"[Mentor] Finding jobs similar to your profile...")
        similar_jobs = query_jobs(resume_text, top_k=5)

    return {
        "jobs_found": len(jobs),
        "jobs_analyzed": len(analyses),
        "top_required_skills": report["top_required_skills"],
        "top_nice_to_have": report["top_nice_to_have"],
        "level_distribution": report["level_distribution"],
        "similar_to_profile": similar_jobs,
        "vector_db_total": collection_count()
    }
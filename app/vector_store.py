import os
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from app.ingestion import JobPosting
from typing import Optional

MODEL_NAME = "all-MiniLM-L6-v2"
CHROMA_PATH = "data/chroma"

model = SentenceTransformer(MODEL_NAME)

client = chromadb.PersistentClient(
    path=CHROMA_PATH,
    settings=Settings(anonymized_telemetry=False)
)

def get_collection(name: str):
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"}
    )

def embed(texts: list[str]) -> list[list[float]]:
    return model.encode(texts, show_progress_bar=True).tolist()

def store_jobs(jobs: list[JobPosting]) -> None:
    collection = get_collection("job_descriptions")
    
    # clear existing jobs before storing new batch
    # so matches are always from the current search
    existing = collection.get()
    if existing["ids"]:
        collection.delete(ids=existing["ids"])
    
    texts = [
        f"{job.title} at {job.company}. {job.description}"
        for job in jobs
    ]
    embeddings = embed(texts)

    collection.upsert(
        ids=[job.id for job in jobs],
        embeddings=embeddings,
        documents=texts,
        metadatas=[{
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "url": job.url,
            "created": job.created or "",
            "salary_min": str(job.salary_min or ""),
            "salary_max": str(job.salary_max or "")
        } for job in jobs]
    )

    print(f"Stored {len(jobs)} jobs in ChromaDB")

def query_jobs(
    query_text: str,
    top_k: int = 5,
    company_filter: Optional[str] = None
) -> list[dict]:
    collection = get_collection("job_descriptions")

    query_embedding = embed([query_text])[0]

    where = {"company": company_filter} if company_filter else None

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where,
        include=["documents", "metadatas", "distances"]
    )

    jobs = []
    for i in range(len(results["ids"][0])):
        jobs.append({
            "id": results["ids"][0][i],
            "title": results["metadatas"][0][i]["title"],
            "company": results["metadatas"][0][i]["company"],
            "location": results["metadatas"][0][i]["location"],
            "url": results["metadatas"][0][i]["url"],
            "similarity": round(1 - results["distances"][0][i], 3),
            "preview": results["documents"][0][i][:300]
        })

    return jobs

def collection_count() -> int:
    collection = get_collection("job_descriptions")
    return collection.count()

if __name__ == "__main__":
    import asyncio
    from app.ingestion import fetch_multiple_roles

    async def main():
        print("Fetching jobs...")
        jobs = await fetch_multiple_roles(
            roles=["AI Engineer", "Machine Learning Engineer", "LLM Engineer"],
            location="New York"
        )

        print(f"\nStoring {len(jobs)} jobs in ChromaDB...")
        store_jobs(jobs)

        print(f"\nTotal in DB: {collection_count()}")

        print("\nQuerying: 'Python developer with LLM and API experience'")
        results = query_jobs(
            "Python developer with LLM and API experience",
            top_k=5
        )

        for r in results:
            print(f"\n{r['title']} @ {r['company']}")
            print(f"Similarity: {r['similarity']}")
            print(f"Location: {r['location']}")
            print(f"URL: {r['url']}")

    asyncio.run(main())
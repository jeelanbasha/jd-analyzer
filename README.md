# JD Analyzer

Small helper that sends job descriptions to Anthropic's Claude model and returns an analysis (required skills, nice-to-have skills, years of experience, experience level, red flags).

**Files**

- `analyzer.py`: main script that calls the Anthropic SDK to analyze job descriptions.

**Requirements**

- Python 3.8+
- `anthropic` Python SDK
- `python-dotenv` (optional, for loading a local `.env` file)

Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install anthropic python-dotenv
```

**Setup**

1. Obtain an Anthropic API key from your Anthropic account.
2. Set the environment variable `ANTHROPIC_API_KEY` (example):

```bash
export ANTHROPIC_API_KEY="sk_..."
```

Alternatively create a `.env` file in the project root with:

```
ANTHROPIC_API_KEY=sk_...
```

and ensure `python-dotenv` is installed and loaded in `analyzer.py` if you want automatic loading.

**Usage**

Run the analyzer against the example sample JD provided in `analyzer.py`:

```bash
python analyzer.py
```

The script will print the model's text response and a small usage dict with token counts.

**Notes & suggestions**

- The current script returns the raw model text in `raw_response`. For reliable machine-readable output, modify the prompt to request strict JSON and parse it with `json.loads()`.
- Ensure your environment has network access and that your API key has appropriate permissions — API usage may incur costs.
- The script assumes the `anthropic` SDK response fields used in `analyzer.py` exist; if you see attribute errors, print the full `message` object to inspect the actual response shape.

**Example**
Given a JD with `Senior Python Engineer` and `5+ years` you should expect the model to identify `Python`, `FastAPI`, `PostgreSQL` as required skills and list Kubernetes/Docker/Redis as nice-to-have.

**Development**

- Add unit tests around the parsing and change the prompt to return strict JSON for deterministic parsing.
- Consider adding a CLI wrapper to analyze files or directories of JDs.

---

Created for the `jd-analyzer` project.

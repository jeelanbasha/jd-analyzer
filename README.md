# JD Analyzer

Analyzes job descriptions using the Claude API and extracts:

- Required skills
- Nice-to-have skills
- Experience level
- Red flags

## How to run

```bash
pip install anthropic python-dotenv
cp .env.example .env  # add your API key
python analyzer.py
```

## Example output

# Job Description Analysis

## 1. Required Skills

- Proficiency in at least one modern programming language (Python, C++, C#, or TypeScript)
- SQL fundamentals
- Hands-on experience with AI-assisted development tools (Claude, GitHub Copilot, or similar)
- Demonstrable portfolio of projects built with AI tools
- Familiarity with data pipeline/ETL concepts
- Experience with at least one cloud environment (AWS preferred)
- Problem-solving and analytical skills
- Communication and teamwork skills

## 2. Nice-to-Have Skills

- Unreal Engine experience
- Unity, OpenGL, or other graphics/simulation frameworks
- ML/AI workflows or training-data preparation
- Experience with Palantir Foundry, dbt, Airflow, or Spark
- Bachelor's or Master's degree in Computer Science, Computer Engineering, Software Engineering, or Game Design/Game Programming

## 3. Years of Experience Required

**1-3 years** (listed as preferred, not required)

## 4. Experience Level

**Junior to Early-Mid Level**

- Title includes "Assist senior engineers"
- Entry-level responsibilities with supervision
- 1-3 years preferred experience range

## 5. Red Flags

⚠️ **Moderate Concerns:**

- **Vague company/mission details** - Mentions "consequential clean energy buildouts" and nuclear energy but doesn't name the company
- **No salary range mentioned** - Lack of compensation transparency
- **"Top talent" rhetoric** - May indicate high pressure or unrealistic expectations for a junior role

⚠️ **Minor Concerns:**

- Emphasis on "AI-assisted coding" as a core skill is relatively novel and may indicate over-reliance on tools
- "Adhere to quality standards & complete assigned tasks within established timelines" suggests potentially rigid deadlines

"""AI extraction of structured profile data from raw resume text.

The output shape mirrors app/schemas/profile.py's ProfileIn closely enough
that the frontend can pre-fill the CV builder form directly from
`cv_documents.parsed_json` - but it is NOT written to the canonical profile
automatically. The user always reviews/edits it first (see
docs/plan: "review screen pre-fills forms").
"""
from app.integrations.ollama_client import OllamaClient

EXTRACTION_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "full_name": {"type": "string"},
        "headline": {"type": "string"},
        "summary": {"type": "string"},
        "location": {"type": "string"},
        "phone": {"type": "string"},
        "email": {"type": "string"},
        "links": {
            "type": "object",
            "properties": {
                "linkedin": {"type": "string"},
                "github": {"type": "string"},
                "website": {"type": "string"},
            },
        },
        "work_experience": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "company": {"type": "string"},
                    "location": {"type": "string"},
                    "start_date": {"type": "string", "description": "YYYY-MM-DD or YYYY-MM, empty if unknown"},
                    "end_date": {"type": "string", "description": "YYYY-MM-DD, empty if still current"},
                    "is_current": {"type": "boolean"},
                    "description": {"type": "string"},
                },
            },
        },
        "education": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "school": {"type": "string"},
                    "degree": {"type": "string"},
                    "field_of_study": {"type": "string"},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                    "description": {"type": "string"},
                },
            },
        },
        "certifications": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "issuer": {"type": "string"},
                    "issue_date": {"type": "string"},
                    "credential_url": {"type": "string"},
                },
            },
        },
        "projects": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "url": {"type": "string"},
                    "technologies": {"type": "string"},
                },
            },
        },
        "languages": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"name": {"type": "string"}, "proficiency": {"type": "string"}},
            },
        },
        "skills": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "category": {"type": "string"},
                    "proficiency": {"type": "string"},
                },
            },
        },
    },
    "required": ["full_name", "work_experience", "education", "skills"],
}

EXTRACTION_SYSTEM_PROMPT = (
    "You extract structured resume data from raw resume text. Be faithful to the source - "
    "do not invent employers, dates, or skills that aren't present. If something is not in "
    "the text, leave that field empty rather than guessing. Dates should be normalized to "
    "YYYY-MM-DD when a day is known, or YYYY-MM when only month/year is known, else leave "
    "empty. Respond with ONLY JSON matching the given schema."
)


async def extract_cv_structured_data(raw_text: str) -> dict:
    client = OllamaClient()
    # Resumes are short enough that a generous but bounded slice keeps
    # prompts fast without truncating real content in practice.
    user_prompt = f"RESUME TEXT:\n{raw_text[:12000]}"
    return await client.generate_json(EXTRACTION_SYSTEM_PROMPT, user_prompt, EXTRACTION_JSON_SCHEMA)

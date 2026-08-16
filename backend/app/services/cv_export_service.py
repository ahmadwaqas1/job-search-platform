"""Renders the canonical (or a tailored) profile into a formatted PDF resume
using WeasyPrint over Jinja2 HTML/CSS templates. Nothing is persisted by
default - profile data is the source of truth, PDF exports are a pure
projection of it, generated on demand.
"""
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

from app.models.profile import Profile

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates" / "cv"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
)

AVAILABLE_TEMPLATES = {"modern": "modern.html", "classic": "classic.html"}


def _fmt_date(d) -> str:
    if not d:
        return ""
    return d.strftime("%b %Y")


_env.filters["fmt_date"] = _fmt_date


def render_profile_pdf(profile: Profile, template_id: str = "modern") -> bytes:
    template_file = AVAILABLE_TEMPLATES.get(template_id, AVAILABLE_TEMPLATES["modern"])
    template = _env.get_template(template_file)
    html_str = template.render(profile=profile)
    return HTML(string=html_str, base_url=str(TEMPLATES_DIR)).write_pdf()


def render_tailored_pdf(
    profile: Profile,
    tailored_summary: str,
    emphasized_skills: list[str],
    template_id: str = "modern",
) -> bytes:
    """Renders a per-application resume variant: same real experience/
    education (never fabricated), just a swapped-in tailored summary and
    the emphasized skills sorted first. Reuses the canonical templates via
    a lightweight object exposing the same attributes as Profile, so no
    parallel dict-rendering path is needed.
    """
    from types import SimpleNamespace

    emphasized_lower = {s.lower() for s in emphasized_skills}
    skills_sorted = sorted(profile.skills, key=lambda s: 0 if s.name.lower() in emphasized_lower else 1)

    shadow = SimpleNamespace(
        full_name=profile.full_name,
        headline=profile.headline,
        summary=tailored_summary or profile.summary,
        location=profile.location,
        phone=profile.phone,
        email=profile.email,
        links=profile.links,
        work_experience=profile.work_experience,
        education=profile.education,
        certifications=profile.certifications,
        projects=profile.projects,
        languages=profile.languages,
        skills=skills_sorted,
    )
    template_file = AVAILABLE_TEMPLATES.get(template_id, AVAILABLE_TEMPLATES["modern"])
    template = _env.get_template(template_file)
    html_str = template.render(profile=shadow)
    return HTML(string=html_str, base_url=str(TEMPLATES_DIR)).write_pdf()

import type { ProfileFormValues } from "@/features/profile/formTypes";

/** Best-effort mapping from the AI extraction's raw JSON (see backend
 * app/services/cv_parser_service.py's EXTRACTION_JSON_SCHEMA) into the
 * CV builder form's shape. Defensive about missing/malformed fields since
 * this is LLM output - the user reviews everything before saving anyway.
 */
export function mapExtractedToFormValues(parsed: Record<string, unknown>, current: ProfileFormValues): ProfileFormValues {
  const str = (v: unknown): string => (typeof v === "string" ? v : "");
  const arr = (v: unknown): Record<string, unknown>[] => (Array.isArray(v) ? (v as Record<string, unknown>[]) : []);
  const links = (parsed.links ?? {}) as Record<string, unknown>;

  return {
    ...current,
    full_name: str(parsed.full_name) || current.full_name,
    headline: str(parsed.headline) || current.headline,
    summary: str(parsed.summary) || current.summary,
    location: str(parsed.location) || current.location,
    phone: str(parsed.phone) || current.phone,
    email: str(parsed.email) || current.email,
    links: {
      linkedin: str(links.linkedin) || current.links.linkedin,
      github: str(links.github) || current.links.github,
      website: str(links.website) || current.links.website,
      other: current.links.other,
    },
    work_experience: arr(parsed.work_experience).map((w) => ({
      title: str(w.title),
      company: str(w.company),
      location: str(w.location),
      start_date: str(w.start_date) || null,
      end_date: str(w.end_date) || null,
      is_current: Boolean(w.is_current),
      description: str(w.description),
    })),
    education: arr(parsed.education).map((e) => ({
      school: str(e.school),
      degree: str(e.degree),
      field_of_study: str(e.field_of_study),
      start_date: str(e.start_date) || null,
      end_date: str(e.end_date) || null,
      description: str(e.description),
    })),
    certifications: arr(parsed.certifications).map((c) => ({
      name: str(c.name),
      issuer: str(c.issuer),
      issue_date: str(c.issue_date) || null,
      credential_url: str(c.credential_url),
    })),
    projects: arr(parsed.projects).map((p) => ({
      name: str(p.name),
      description: str(p.description),
      url: str(p.url),
      technologies: str(p.technologies),
    })),
    languages: arr(parsed.languages).map((l) => ({ name: str(l.name), proficiency: str(l.proficiency) })),
    skills: arr(parsed.skills).map((s) => ({
      name: str(s.name),
      category: str(s.category),
      proficiency: str(s.proficiency),
    })),
  };
}

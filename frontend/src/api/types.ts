/**
 * Hand-written mirror of the backend's Pydantic response/request schemas
 * (see backend/app/schemas/*.py). This is a stand-in for real codegen -
 * once the backend is running, `npm run generate:types` (openapi-typescript
 * against /openapi.json) produces schema.d.ts from the live OpenAPI spec;
 * prefer that once available and keep this file's shapes in sync manually
 * until then.
 */

export interface User {
  id: string;
  email: string;
  is_active: boolean;
}

export interface ProfileLinks {
  linkedin: string;
  github: string;
  website: string;
  other: string;
}

export interface WorkExperience {
  id?: string;
  title: string;
  company: string;
  location: string;
  start_date: string | null;
  end_date: string | null;
  is_current: boolean;
  description: string;
}

export interface Education {
  id?: string;
  school: string;
  degree: string;
  field_of_study: string;
  start_date: string | null;
  end_date: string | null;
  description: string;
}

export interface Certification {
  id?: string;
  name: string;
  issuer: string;
  issue_date: string | null;
  credential_url: string;
}

export interface ProjectItem {
  id?: string;
  name: string;
  description: string;
  url: string;
  technologies: string;
}

export interface LanguageItem {
  id?: string;
  name: string;
  proficiency: string;
}

export interface Skill {
  id?: string;
  name: string;
  category: string;
  proficiency: string;
}

export interface Profile {
  id: string;
  full_name: string;
  headline: string;
  summary: string;
  location: string;
  phone: string;
  email: string;
  links: ProfileLinks;
  work_experience: WorkExperience[];
  education: Education[];
  certifications: Certification[];
  projects: ProjectItem[];
  languages: LanguageItem[];
  skills: Skill[];
  has_embedding: boolean;
}

export interface CVDocument {
  id: string;
  kind: "uploaded" | "generated";
  original_filename: string;
  mime_type: string;
  parse_status: "pending" | "processing" | "parsed" | "failed";
  parse_error: string;
  parsed_json: Record<string, unknown> | null;
}

export interface JobSource {
  id: string;
  user_id: string | null;
  type: string;
  name: string;
  config: Record<string, unknown>;
  poll_interval_minutes: number;
  last_polled_at: string | null;
  last_poll_status: string;
  last_poll_error: string;
  is_active: boolean;
}

export interface JobPosting {
  id: string;
  title: string;
  company: string;
  location: string;
  remote_type: "remote" | "hybrid" | "onsite" | "unknown";
  description_text: string;
  salary_min: number | null;
  salary_max: number | null;
  salary_currency: string;
  salary_period: string;
  url: string;
  apply_url: string;
  posted_at: string | null;
  tags: string[];
  source_id: string;
}

export interface Match {
  id: string;
  job_posting_id: string;
  similarity_score: number;
  llm_score: number | null;
  explanation_text: string;
  matched_skills: string[];
  missing_skills: string[];
  status: string;
  computed_at: string | null;
  job_posting: JobPosting;
}

export type ApplicationStatus = "saved" | "applied" | "interviewing" | "offer" | "rejected" | "withdrawn";

export interface ApplicationAnswer {
  question: string;
  answer: string;
}

export interface ApplicationEvent {
  id: string;
  event_type: string;
  from_status: string;
  to_status: string;
  note: string;
  created_at: string;
}

export interface Application {
  id: string;
  status: ApplicationStatus;
  draft_status: "none" | "generating" | "ready" | "failed";
  cover_letter_text: string;
  application_answers: ApplicationAnswer[];
  applied_via: "manual" | "auto_api";
  applied_at: string | null;
  notes: string;
  tailored_resume_cv_document_id: string | null;
  job_posting: JobPosting;
  events: ApplicationEvent[];
  created_at: string;
}

export interface SalarySnapshot {
  role_title: string;
  location: string;
  source: "adzuna" | "usajobs" | "bls" | "aggregated_postings";
  currency: string;
  period: string;
  p10: number | null;
  median: number | null;
  p90: number | null;
  sample_size: number;
  fetched_at: string | null;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  created_at: string;
}

export interface ChatSession {
  id: string;
  title: string;
  job_posting_id: string | null;
  created_at: string;
  messages: ChatMessage[];
}

export interface ChatSessionSummary {
  id: string;
  title: string;
  job_posting_id: string | null;
  created_at: string;
}

export interface EffectiveSettings {
  ollama_base_url: string;
  ollama_chat_model: string;
  ollama_embed_model: string;
  max_upload_mb: number;
  default_job_poll_interval_minutes: number;
  adzuna_configured: boolean;
  usajobs_configured: boolean;
  bls_configured: boolean;
}

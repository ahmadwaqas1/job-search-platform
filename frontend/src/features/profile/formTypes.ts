/**
 * Shape of the CV builder form, plus the validation rules for it. Lives in
 * its own file (rather than inside ProfileForm.tsx) so the individual
 * section components can import the type without creating an import cycle
 * back to ProfileForm.tsx itself.
 */
import { z } from "zod";

import type { Profile } from "@/api/types";

export type ProfileFormValues = Omit<Profile, "id" | "has_embedding">;

const optionalStr = z.string().optional().default("");

export const profileFormSchema = z.object({
  full_name: z.string().min(1, "Required"),
  headline: optionalStr,
  summary: optionalStr,
  location: optionalStr,
  phone: optionalStr,
  email: z.string().email().or(z.literal("")),
  links: z.object({
    linkedin: optionalStr,
    github: optionalStr,
    website: optionalStr,
    other: optionalStr,
  }),
  work_experience: z.array(
    z.object({
      title: optionalStr,
      company: optionalStr,
      location: optionalStr,
      start_date: z.string().nullable().optional(),
      end_date: z.string().nullable().optional(),
      is_current: z.boolean().default(false),
      description: optionalStr,
    })
  ),
  education: z.array(
    z.object({
      school: optionalStr,
      degree: optionalStr,
      field_of_study: optionalStr,
      start_date: z.string().nullable().optional(),
      end_date: z.string().nullable().optional(),
      description: optionalStr,
    })
  ),
  certifications: z.array(
    z.object({
      name: optionalStr,
      issuer: optionalStr,
      issue_date: z.string().nullable().optional(),
      credential_url: optionalStr,
    })
  ),
  projects: z.array(
    z.object({
      name: optionalStr,
      description: optionalStr,
      url: optionalStr,
      technologies: optionalStr,
    })
  ),
  languages: z.array(z.object({ name: optionalStr, proficiency: optionalStr })),
  skills: z.array(z.object({ name: z.string().min(1, "Required"), category: optionalStr, proficiency: optionalStr })),
});

export const EMPTY_PROFILE: ProfileFormValues = {
  full_name: "",
  headline: "",
  summary: "",
  location: "",
  phone: "",
  email: "",
  links: { linkedin: "", github: "", website: "", other: "" },
  work_experience: [],
  education: [],
  certifications: [],
  projects: [],
  languages: [],
  skills: [],
};

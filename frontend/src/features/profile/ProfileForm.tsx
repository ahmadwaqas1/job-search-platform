/**
 * The CV builder form. This component only wires things up - it creates
 * the react-hook-form instance and one useFieldArray per repeatable CV
 * section, then hands each section's slice of that state down to a small,
 * focused component in ./sections/. Look there for the actual fields.
 */
import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect } from "react";
import { useFieldArray, useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { profileFormSchema, type ProfileFormValues } from "@/features/profile/formTypes";
import { BasicsSection } from "@/features/profile/sections/BasicsSection";
import { CertificationsSection } from "@/features/profile/sections/CertificationsSection";
import { EducationSection } from "@/features/profile/sections/EducationSection";
import { ExperienceSection } from "@/features/profile/sections/ExperienceSection";
import { LanguagesSection } from "@/features/profile/sections/LanguagesSection";
import { ProjectsSection } from "@/features/profile/sections/ProjectsSection";
import { SkillsSection } from "@/features/profile/sections/SkillsSection";

interface Props {
  defaultValues: ProfileFormValues;
  onSubmit: (values: ProfileFormValues) => void;
  isSaving: boolean;
  /** Bumped whenever new CV-extracted data should overwrite the form. */
  resetSignal: number;
}

export function ProfileForm({ defaultValues, onSubmit, isSaving, resetSignal }: Props) {
  const {
    register,
    control,
    handleSubmit,
    reset,
    formState: { errors, isDirty },
  } = useForm<ProfileFormValues>({
    resolver: zodResolver(profileFormSchema),
    defaultValues,
  });

  // Re-fill the whole form whenever the parent loads new default values
  // (profile finished loading, or the user imported a CV) - resetSignal is
  // just a counter the parent bumps to trigger this, since `defaultValues`
  // itself is a new object reference on every render.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => reset(defaultValues), [resetSignal]);

  const experience = useFieldArray({ control, name: "work_experience" });
  const education = useFieldArray({ control, name: "education" });
  const certifications = useFieldArray({ control, name: "certifications" });
  const projects = useFieldArray({ control, name: "projects" });
  const languages = useFieldArray({ control, name: "languages" });
  const skills = useFieldArray({ control, name: "skills" });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-8">
      <BasicsSection register={register} fullNameError={errors.full_name?.message} />
      <ExperienceSection register={register} fieldArray={experience} />
      <EducationSection register={register} fieldArray={education} />
      <SkillsSection register={register} fieldArray={skills} />
      <ProjectsSection register={register} fieldArray={projects} />
      <CertificationsSection register={register} fieldArray={certifications} />
      <LanguagesSection register={register} fieldArray={languages} />

      <div className="sticky bottom-4 flex justify-end">
        <Button type="submit" size="lg" disabled={isSaving} className="shadow-lg">
          {isSaving ? "Saving..." : isDirty ? "Save profile" : "Saved"}
        </Button>
      </div>
    </form>
  );
}

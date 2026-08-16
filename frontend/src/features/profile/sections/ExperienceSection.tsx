import type { UseFieldArrayReturn, UseFormRegister } from "react-hook-form";

import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import type { ProfileFormValues } from "@/features/profile/formTypes";
import { Field, RemoveButton, Section } from "@/features/profile/sections/shared";

const BLANK_EXPERIENCE = {
  title: "",
  company: "",
  location: "",
  start_date: "",
  end_date: "",
  is_current: false,
  description: "",
};

export function ExperienceSection({
  register,
  fieldArray,
}: {
  register: UseFormRegister<ProfileFormValues>;
  fieldArray: UseFieldArrayReturn<ProfileFormValues, "work_experience">;
}) {
  const { fields, append, remove } = fieldArray;

  return (
    <Section title="Work Experience" onAdd={() => append(BLANK_EXPERIENCE)}>
      {fields.map((f, i) => (
        <div key={f.id} className="flex flex-col gap-2 rounded-md border border-border p-3">
          <div className="grid grid-cols-2 gap-3">
            <Field label="Title">
              <Input {...register(`work_experience.${i}.title`)} />
            </Field>
            <Field label="Company">
              <Input {...register(`work_experience.${i}.company`)} />
            </Field>
            <Field label="Location">
              <Input {...register(`work_experience.${i}.location`)} />
            </Field>
            <div className="flex items-end gap-2">
              <Field label="Start" className="flex-1">
                <Input type="date" {...register(`work_experience.${i}.start_date`)} />
              </Field>
              <Field label="End" className="flex-1">
                <Input type="date" {...register(`work_experience.${i}.end_date`)} />
              </Field>
            </div>
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" {...register(`work_experience.${i}.is_current`)} />
            Current role
          </label>
          <Field label="Description">
            <Textarea rows={3} {...register(`work_experience.${i}.description`)} />
          </Field>
          <RemoveButton onClick={() => remove(i)} />
        </div>
      ))}
    </Section>
  );
}

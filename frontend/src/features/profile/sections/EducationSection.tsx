import type { UseFieldArrayReturn, UseFormRegister } from "react-hook-form";

import { Input } from "@/components/ui/input";
import type { ProfileFormValues } from "@/features/profile/formTypes";
import { Field, RemoveButton, Section } from "@/features/profile/sections/shared";

const BLANK_EDUCATION = { school: "", degree: "", field_of_study: "", start_date: "", end_date: "", description: "" };

export function EducationSection({
  register,
  fieldArray,
}: {
  register: UseFormRegister<ProfileFormValues>;
  fieldArray: UseFieldArrayReturn<ProfileFormValues, "education">;
}) {
  const { fields, append, remove } = fieldArray;

  return (
    <Section title="Education" onAdd={() => append(BLANK_EDUCATION)}>
      {fields.map((f, i) => (
        <div key={f.id} className="flex flex-col gap-2 rounded-md border border-border p-3">
          <div className="grid grid-cols-2 gap-3">
            <Field label="School">
              <Input {...register(`education.${i}.school`)} />
            </Field>
            <Field label="Degree">
              <Input {...register(`education.${i}.degree`)} />
            </Field>
            <Field label="Field of study">
              <Input {...register(`education.${i}.field_of_study`)} />
            </Field>
            <div className="flex items-end gap-2">
              <Field label="Start" className="flex-1">
                <Input type="date" {...register(`education.${i}.start_date`)} />
              </Field>
              <Field label="End" className="flex-1">
                <Input type="date" {...register(`education.${i}.end_date`)} />
              </Field>
            </div>
          </div>
          <RemoveButton onClick={() => remove(i)} />
        </div>
      ))}
    </Section>
  );
}

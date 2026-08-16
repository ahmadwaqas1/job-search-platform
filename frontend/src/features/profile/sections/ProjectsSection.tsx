import type { UseFieldArrayReturn, UseFormRegister } from "react-hook-form";

import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import type { ProfileFormValues } from "@/features/profile/formTypes";
import { Field, RemoveButton, Section } from "@/features/profile/sections/shared";

export function ProjectsSection({
  register,
  fieldArray,
}: {
  register: UseFormRegister<ProfileFormValues>;
  fieldArray: UseFieldArrayReturn<ProfileFormValues, "projects">;
}) {
  const { fields, append, remove } = fieldArray;

  return (
    <Section title="Projects" onAdd={() => append({ name: "", description: "", url: "", technologies: "" })}>
      {fields.map((f, i) => (
        <div key={f.id} className="flex flex-col gap-2 rounded-md border border-border p-3">
          <div className="grid grid-cols-2 gap-3">
            <Field label="Name">
              <Input {...register(`projects.${i}.name`)} />
            </Field>
            <Field label="Technologies">
              <Input {...register(`projects.${i}.technologies`)} />
            </Field>
          </div>
          <Field label="Description">
            <Textarea rows={2} {...register(`projects.${i}.description`)} />
          </Field>
          <RemoveButton onClick={() => remove(i)} />
        </div>
      ))}
    </Section>
  );
}

import type { UseFieldArrayReturn, UseFormRegister } from "react-hook-form";

import { Input } from "@/components/ui/input";
import type { ProfileFormValues } from "@/features/profile/formTypes";
import { Field, RemoveButton, Section } from "@/features/profile/sections/shared";

export function CertificationsSection({
  register,
  fieldArray,
}: {
  register: UseFormRegister<ProfileFormValues>;
  fieldArray: UseFieldArrayReturn<ProfileFormValues, "certifications">;
}) {
  const { fields, append, remove } = fieldArray;

  return (
    <Section title="Certifications" onAdd={() => append({ name: "", issuer: "", issue_date: "", credential_url: "" })}>
      {fields.map((f, i) => (
        <div key={f.id} className="grid grid-cols-2 gap-3 rounded-md border border-border p-3">
          <Field label="Name">
            <Input {...register(`certifications.${i}.name`)} />
          </Field>
          <Field label="Issuer">
            <Input {...register(`certifications.${i}.issuer`)} />
          </Field>
          <Field label="Issue date">
            <Input type="date" {...register(`certifications.${i}.issue_date`)} />
          </Field>
          <div className="flex items-end">
            <RemoveButton onClick={() => remove(i)} />
          </div>
        </div>
      ))}
    </Section>
  );
}

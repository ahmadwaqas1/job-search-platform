import { Trash2 } from "lucide-react";
import type { UseFieldArrayReturn, UseFormRegister } from "react-hook-form";

import { Input } from "@/components/ui/input";
import type { ProfileFormValues } from "@/features/profile/formTypes";
import { Section } from "@/features/profile/sections/shared";

export function LanguagesSection({
  register,
  fieldArray,
}: {
  register: UseFormRegister<ProfileFormValues>;
  fieldArray: UseFieldArrayReturn<ProfileFormValues, "languages">;
}) {
  const { fields, append, remove } = fieldArray;

  return (
    <Section title="Languages" onAdd={() => append({ name: "", proficiency: "" })}>
      <div className="flex flex-wrap gap-2">
        {fields.map((f, i) => (
          <div key={f.id} className="flex items-center gap-1 rounded-md border border-border p-1.5">
            <Input className="h-7 w-32" placeholder="Language" {...register(`languages.${i}.name`)} />
            <Input className="h-7 w-28" placeholder="Fluency" {...register(`languages.${i}.proficiency`)} />
            <button type="button" onClick={() => remove(i)} className="p-1 text-muted-foreground hover:text-destructive">
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          </div>
        ))}
      </div>
    </Section>
  );
}

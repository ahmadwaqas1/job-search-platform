import { Trash2 } from "lucide-react";
import type { UseFieldArrayReturn, UseFormRegister } from "react-hook-form";

import { Input } from "@/components/ui/input";
import type { ProfileFormValues } from "@/features/profile/formTypes";
import { Section } from "@/features/profile/sections/shared";

export function SkillsSection({
  register,
  fieldArray,
}: {
  register: UseFormRegister<ProfileFormValues>;
  fieldArray: UseFieldArrayReturn<ProfileFormValues, "skills">;
}) {
  const { fields, append, remove } = fieldArray;

  return (
    <Section title="Skills" onAdd={() => append({ name: "", category: "", proficiency: "" })}>
      <div className="flex flex-wrap gap-2">
        {fields.map((f, i) => (
          <div key={f.id} className="flex items-center gap-1 rounded-md border border-border p-1.5">
            <Input className="h-7 w-40" placeholder="Skill" {...register(`skills.${i}.name`)} />
            <button type="button" onClick={() => remove(i)} className="p-1 text-muted-foreground hover:text-destructive">
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          </div>
        ))}
      </div>
    </Section>
  );
}

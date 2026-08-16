import type { UseFormRegister } from "react-hook-form";

import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import type { ProfileFormValues } from "@/features/profile/formTypes";
import { Field, Section } from "@/features/profile/sections/shared";

export function BasicsSection({
  register,
  fullNameError,
}: {
  register: UseFormRegister<ProfileFormValues>;
  fullNameError?: string;
}) {
  return (
    <Section title="Basics">
      <div className="grid grid-cols-2 gap-3">
        <Field label="Full name" error={fullNameError}>
          <Input {...register("full_name")} />
        </Field>
        <Field label="Headline" hint="e.g. Senior Backend Engineer">
          <Input {...register("headline")} />
        </Field>
        <Field label="Email">
          <Input type="email" {...register("email")} />
        </Field>
        <Field label="Phone">
          <Input {...register("phone")} />
        </Field>
        <Field label="Location">
          <Input {...register("location")} placeholder="City, Country" />
        </Field>
      </div>
      <Field label="Summary">
        <Textarea rows={4} {...register("summary")} placeholder="2-4 sentence professional summary" />
      </Field>
      <div className="grid grid-cols-3 gap-3">
        <Field label="LinkedIn">
          <Input {...register("links.linkedin")} />
        </Field>
        <Field label="GitHub">
          <Input {...register("links.github")} />
        </Field>
        <Field label="Website">
          <Input {...register("links.website")} />
        </Field>
      </div>
    </Section>
  );
}

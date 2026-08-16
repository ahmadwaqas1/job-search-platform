/**
 * Small pieces of markup reused by every CV builder section below:
 * - <Section>   a titled block with an optional "+ Add" button
 * - <Field>     a label + input/textarea + optional hint or error text
 * - <RemoveButton> the "trash can" button under a repeatable list item
 *
 * Pulling these out here means each *Section.tsx file only has to contain
 * the fields specific to that part of the CV, not this repeated wrapper
 * markup.
 */
import { Plus, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";

export function Section({ title, onAdd, children }: { title: string; onAdd?: () => void; children: React.ReactNode }) {
  return (
    <section className="flex flex-col gap-3">
      <div className="flex items-center justify-between border-b border-border pb-2">
        <h2 className="text-lg font-semibold">{title}</h2>
        {onAdd && (
          <Button type="button" variant="outline" size="sm" onClick={onAdd}>
            <Plus className="h-3.5 w-3.5" /> Add
          </Button>
        )}
      </div>
      {children}
    </section>
  );
}

export function Field({
  label,
  hint,
  error,
  className,
  children,
}: {
  label: string;
  hint?: string;
  error?: string;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <div className={`flex flex-col gap-1 ${className ?? ""}`}>
      <Label>{label}</Label>
      {children}
      {hint && !error && <p className="text-xs text-muted-foreground">{hint}</p>}
      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  );
}

export function RemoveButton({ onClick }: { onClick: () => void }) {
  return (
    <Button type="button" variant="ghost" size="sm" onClick={onClick} className="w-fit text-destructive hover:text-destructive">
      <Trash2 className="h-3.5 w-3.5" /> Remove
    </Button>
  );
}

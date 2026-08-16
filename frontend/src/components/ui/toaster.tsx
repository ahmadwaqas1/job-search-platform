import { X } from "lucide-react";

import { cn } from "@/lib/utils";
import { useToastStore } from "@/store/toastStore";

export function Toaster() {
  const { toasts, dismiss } = useToastStore();

  return (
    <div className="fixed bottom-4 right-4 z-[100] flex w-full max-w-sm flex-col gap-2">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={cn(
            "flex items-start gap-2 rounded-lg border border-border bg-card p-3 shadow-lg",
            t.variant === "destructive" && "border-destructive/40 bg-destructive/10",
            t.variant === "success" && "border-emerald-500/40 bg-emerald-500/10"
          )}
        >
          <div className="flex-1">
            <p className="text-sm font-medium">{t.title}</p>
            {t.description && <p className="text-sm text-muted-foreground">{t.description}</p>}
          </div>
          <button onClick={() => dismiss(t.id)} className="rounded p-0.5 hover:bg-accent" aria-label="Dismiss">
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      ))}
    </div>
  );
}

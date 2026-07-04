"use client";

import type { LucideIcon } from "lucide-react";
import { AlertTriangle } from "lucide-react";

/**
 * A clearly-labeled AI-transparency zone. The report separates what was *found*
 * (Retrieved Evidence) from what the AI *concluded* (AI Interpretation) from the
 * clinician *takeaway* (Clinical Summary) — these are never mixed.
 */
export function TransparencyLayer({
  label,
  description,
  icon: Icon,
  children,
}: {
  label: string;
  description: string;
  icon: LucideIcon;
  children: React.ReactNode;
}) {
  return (
    <section className="space-y-4">
      <div className="flex items-start gap-3 rounded-lg border border-border bg-muted/30 p-4">
        <div className="grid size-9 shrink-0 place-items-center rounded-full border border-border bg-background text-primary">
          <Icon className="size-4" />
        </div>
        <div className="space-y-0.5">
          <h2 className="text-base font-semibold tracking-tight">{label}</h2>
          <p className="text-sm text-muted-foreground">{description}</p>
        </div>
      </div>
      <div className="space-y-4">{children}</div>
    </section>
  );
}

/** Quality-control callout: retrieved evidence points in conflicting directions. */
export function ConflictBanner({ conflicts }: { conflicts: string[] }) {
  if (!conflicts.length) return null;
  return (
    <div className="rounded-lg border border-conf-moderate/40 bg-conf-moderate/10 p-4">
      <div className="flex items-center gap-2 text-sm font-medium text-conf-moderate">
        <AlertTriangle className="size-4" /> Conflicting evidence detected
      </div>
      <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-foreground/85">
        {conflicts.map((c, i) => (
          <li key={i}>{c}</li>
        ))}
      </ul>
    </div>
  );
}

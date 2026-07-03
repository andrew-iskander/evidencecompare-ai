import { ShieldCheck, ShieldAlert, ShieldQuestion } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Confidence } from "@/types/report";

const MAP: Record<
  Confidence,
  { label: string; className: string; icon: typeof ShieldCheck }
> = {
  high: {
    label: "High confidence",
    className: "bg-conf-high/15 text-conf-high border-conf-high/30",
    icon: ShieldCheck,
  },
  moderate: {
    label: "Moderate confidence",
    className: "bg-conf-moderate/15 text-conf-moderate border-conf-moderate/30",
    icon: ShieldCheck,
  },
  low: {
    label: "Low confidence",
    className: "bg-conf-low/15 text-conf-low border-conf-low/30",
    icon: ShieldAlert,
  },
  very_low: {
    label: "Very low / insufficient",
    className: "bg-conf-verylow/15 text-conf-verylow border-conf-verylow/30",
    icon: ShieldQuestion,
  },
};

export function ConfidenceBadge({
  level,
  className,
}: {
  level: Confidence;
  className?: string;
}) {
  const { label, className: tone, icon: Icon } = MAP[level];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium",
        tone,
        className,
      )}
    >
      <Icon className="size-3.5" />
      {label}
    </span>
  );
}

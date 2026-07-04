"use client";

import { Fragment, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ChevronRight } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { StudyDesign, TrialExtraction } from "@/types/report";

const DESIGN_LABEL: Record<StudyDesign, string> = {
  meta_analysis: "Meta-analysis",
  systematic_review: "Systematic review",
  guideline: "Guideline",
  rct: "RCT",
  trial_registry: "Registered trial",
  drug_label: "Drug label",
  other: "Study",
};

function Effect({ e }: { e: TrialExtraction }) {
  const parts = [e.hazardRatio, e.relativeRisk, e.confidenceInterval, e.pValue].filter(
    Boolean,
  );
  if (parts.length === 0)
    return <span className="text-muted-foreground">Not reported</span>;
  return <span className="tabular-nums">{parts.join("; ")}</span>;
}

/**
 * Retrieved-evidence layer: structured data the Trial-Extraction agent pulled
 * from each study. Values are extracted from the source text — empty fields show
 * "Not reported" rather than an inferred number (anti-hallucination).
 */
export function TrialDataTable({ extractions }: { extractions: TrialExtraction[] }) {
  const [open, setOpen] = useState<Set<string>>(new Set());
  if (!extractions.length) return null;

  const toggle = (k: string) =>
    setOpen((prev) => {
      const next = new Set(prev);
      if (next.has(k)) next.delete(k);
      else next.add(k);
      return next;
    });

  return (
    <Card className="overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[720px] border-collapse text-sm">
          <thead>
            <tr className="border-b border-border bg-muted/50 text-left">
              <th className="w-8 px-2 py-3" />
              <th className="px-4 py-3 font-medium text-muted-foreground">Study</th>
              <th className="px-4 py-3 font-medium text-muted-foreground">Population</th>
              <th className="px-4 py-3 font-medium text-muted-foreground">
                Intervention / Comparator
              </th>
              <th className="px-4 py-3 font-medium text-muted-foreground">Effect size</th>
            </tr>
          </thead>
          <tbody>
            {extractions.map((e) => {
              const isOpen = open.has(e.refKey);
              const design = e.studyDesign ? DESIGN_LABEL[e.studyDesign] : "Study";
              return (
                <Fragment key={e.refKey}>
                  <tr
                    className="cursor-pointer border-b border-border/60 align-top hover:bg-muted/30"
                    onClick={() => toggle(e.refKey)}
                  >
                    <td className="px-2 py-3 text-muted-foreground">
                      <ChevronRight
                        className={`size-4 transition-transform ${isOpen ? "rotate-90" : ""}`}
                      />
                    </td>
                    <td className="max-w-[280px] px-4 py-3">
                      <div className="flex items-center gap-1.5">
                        <Badge variant="outline">[{e.refKey.replace("c", "")}]</Badge>
                        <Badge variant="muted">{design}</Badge>
                      </div>
                      <p className="mt-1 line-clamp-2 text-foreground/90" title={e.title}>
                        {e.title}
                      </p>
                    </td>
                    <td className="px-4 py-3 text-foreground/80">
                      {e.population ?? (
                        <span className="text-muted-foreground">Not reported</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-foreground/80">
                      <span className="text-primary">{e.intervention ?? "—"}</span>
                      <span className="text-muted-foreground"> vs </span>
                      <span>{e.comparator ?? "—"}</span>
                      {typeof e.sampleSize === "number" && (
                        <div className="text-xs text-muted-foreground">
                          n = {e.sampleSize.toLocaleString()}
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <Effect e={e} />
                    </td>
                  </tr>
                  <AnimatePresence initial={false}>
                    {isOpen && (
                      <motion.tr
                        key={`${e.refKey}-detail`}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="border-b border-border/60 bg-muted/20"
                      >
                        <td />
                        <td colSpan={4} className="px-4 pb-4 pt-0">
                          <div className="grid gap-3 sm:grid-cols-3">
                            <Detail label="Outcomes" items={e.outcomes} />
                            <Detail label="Adverse events" items={e.adverseEvents} />
                            <Detail label="Strengths" items={e.strengths} />
                            <Detail label="Limitations" items={e.limitations} />
                          </div>
                          {e.extractorModel && (
                            <p className="mt-3 text-xs text-muted-foreground">
                              Extracted by {e.extractorModel}
                            </p>
                          )}
                        </td>
                      </motion.tr>
                    )}
                  </AnimatePresence>
                </Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

function Detail({ label, items }: { label: string; items: string[] }) {
  return (
    <div>
      <p className="text-xs font-medium text-muted-foreground">{label}</p>
      {items.length ? (
        <ul className="mt-1 list-inside list-disc space-y-0.5 text-sm text-foreground/85">
          {items.map((it, i) => (
            <li key={i}>{it}</li>
          ))}
        </ul>
      ) : (
        <p className="mt-1 text-sm text-muted-foreground">None reported</p>
      )}
    </div>
  );
}

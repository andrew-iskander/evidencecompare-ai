"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ChevronDown,
  FlaskConical,
  ListChecks,
  ShieldAlert,
  Timer,
  GitCompareArrows,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import type { Report } from "@/types/report";

/**
 * Transparency Mode — the optional "Research Process" panel. Hidden by default;
 * advanced users can expand it to see exactly what the twelve-agent pipeline did:
 * the queries executed, how many studies were found/excluded, the ranking and
 * verification decisions, the comparative safety matrix, conflict reconciliation,
 * and per-agent processing time. It exposes the pipeline's work without changing
 * the clean default report view.
 */
export function ResearchProcessPanel({ report }: { report: Report }) {
  const [open, setOpen] = useState(false);
  const rp = report.researchProcess;
  const scores = report.scores;
  if (!rp && !scores) return null;

  const snap = rp?.snapshot ?? {};
  const queries = (snap.queries as string[] | undefined) ?? [];
  const candidates = (snap.candidates as number | undefined) ?? 0;
  const ranked = (snap.ranked as number | undefined) ?? 0;
  const verification = rp?.verification ?? null;
  const verified = verification?.verified ?? 0;
  const removed = verification?.removed ?? 0;
  const excluded = Math.max(0, candidates - verified);
  const overall = scores?.overall as Record<string, unknown> | undefined;
  const logs = rp?.logs ?? [];
  const totalMs = Object.values(rp?.timings ?? {}).reduce((a, b) => a + b, 0);

  return (
    <section className="rounded-lg border border-border bg-muted/20">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between gap-3 p-4 text-left"
        aria-expanded={open}
      >
        <span className="flex items-center gap-3">
          <span className="grid size-9 shrink-0 place-items-center rounded-full border border-border bg-background text-primary">
            <FlaskConical className="size-4" />
          </span>
          <span className="space-y-0.5">
            <span className="block text-base font-semibold tracking-tight">
              Research Process
            </span>
            <span className="block text-sm text-muted-foreground">
              How the multi-agent pipeline produced this report — queries, ranking,
              verification, safety, conflicts, and timing.
            </span>
          </span>
        </span>
        <ChevronDown
          className={cn(
            "size-5 shrink-0 text-muted-foreground transition-transform",
            open && "rotate-180",
          )}
        />
      </button>

      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="space-y-6 border-t border-border p-4">
              {/* Retrieval funnel */}
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                <Stat label="Candidates found" value={candidates} />
                <Stat label="Ranked / selected" value={ranked} />
                <Stat label="Citations verified" value={verified} />
                <Stat label="Excluded" value={excluded} />
              </div>

              {/* Evidence confidence + ranking decisions */}
              {overall && (
                <Block icon={ListChecks} title="Evidence ranking decisions">
                  <div className="flex flex-wrap gap-2 text-xs">
                    <Badge>Confidence: {String(overall.confidence)}</Badge>
                    <Badge>Evidence {String(overall.evidence_score)}/100</Badge>
                    <Badge>Consistency {String(overall.consistency_score)}/100</Badge>
                    <Badge>Risk of bias: {String(overall.risk_of_bias)}</Badge>
                  </div>
                  {overall.rationale ? (
                    <p className="mt-2 text-xs text-muted-foreground">
                      {String(overall.rationale)}
                    </p>
                  ) : null}
                  {scores?.studies?.length ? (
                    <div className="mt-3 overflow-x-auto">
                      <table className="w-full min-w-[420px] text-left text-xs">
                        <thead className="text-muted-foreground">
                          <tr>
                            <th className="py-1 pr-3 font-medium">Ref</th>
                            <th className="py-1 pr-3 font-medium">Tier</th>
                            <th className="py-1 pr-3 font-medium">Evidence</th>
                            <th className="py-1 pr-3 font-medium">Risk of bias</th>
                          </tr>
                        </thead>
                        <tbody>
                          {scores.studies.slice(0, 8).map((s, i) => (
                            <tr key={i} className="border-t border-border/60">
                              <td className="py-1 pr-3 font-mono">{String(s.ref_key)}</td>
                              <td className="py-1 pr-3">{String(s.tier_label)}</td>
                              <td className="py-1 pr-3">{String(s.evidence_score)}/100</td>
                              <td className="py-1 pr-3">{String(s.risk_of_bias)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : null}
                </Block>
              )}

              {/* Queries executed */}
              {queries.length > 0 && (
                <Block icon={FlaskConical} title="Search queries executed">
                  <ul className="space-y-1">
                    {queries.map((q, i) => (
                      <li
                        key={i}
                        className="rounded bg-background px-2 py-1 font-mono text-xs text-foreground/85"
                      >
                        {q}
                      </li>
                    ))}
                  </ul>
                </Block>
              )}

              {/* Comparative safety matrix */}
              {report.safetyMatrix?.rows?.length ? (
                <Block icon={ShieldAlert} title="Comparative safety matrix">
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[420px] text-left text-xs">
                      <thead className="text-muted-foreground">
                        <tr>
                          <th className="py-1 pr-3 font-medium">Domain</th>
                          <th className="py-1 pr-3 font-medium">{report.moleculeA}</th>
                          <th className="py-1 pr-3 font-medium">{report.moleculeB}</th>
                        </tr>
                      </thead>
                      <tbody>
                        {report.safetyMatrix.rows.map((row) => (
                          <tr key={row.key} className="border-t border-border/60 align-top">
                            <td className="py-1 pr-3 font-medium">{row.label}</td>
                            <SafetyTd note={row.a.note} reported={row.a.status === "reported"} />
                            <SafetyTd note={row.b.note} reported={row.b.status === "reported"} />
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </Block>
              ) : null}

              {/* Conflict reconciliation */}
              {report.reconciliation && (
                <Block icon={GitCompareArrows} title="Conflict reconciliation">
                  <p className="text-xs text-muted-foreground">
                    {report.reconciliation.summary}
                  </p>
                  {report.reconciliation.explanations.map((ex, i) => (
                    <p key={i} className="mt-2 text-xs text-foreground/85">
                      {ex.text}
                    </p>
                  ))}
                </Block>
              )}

              {/* Verification + processing time */}
              <Block icon={Timer} title="Verification & processing time">
                <div className="flex flex-wrap gap-2 text-xs">
                  {verification && (
                    <Badge>
                      Verified {verification.verified}/{verification.checked}
                      {removed ? ` · removed ${removed}` : ""}
                    </Badge>
                  )}
                  <Badge>Total {Math.round(totalMs)} ms</Badge>
                </div>
                {logs.length > 0 && (
                  <div className="mt-3 overflow-x-auto">
                    <table className="w-full min-w-[520px] text-left text-xs">
                      <thead className="text-muted-foreground">
                        <tr>
                          <th className="py-1 pr-3 font-medium">Agent</th>
                          <th className="py-1 pr-3 font-medium">Model</th>
                          <th className="py-1 pr-3 font-medium">Detail</th>
                          <th className="py-1 pr-3 font-medium">ms</th>
                        </tr>
                      </thead>
                      <tbody>
                        {logs.map((l, i) => (
                          <tr key={i} className="border-t border-border/60 align-top">
                            <td className="py-1 pr-3 font-medium">{l.label}</td>
                            <td className="py-1 pr-3 font-mono text-[11px]">
                              {l.model ?? "—"}
                            </td>
                            <td className="py-1 pr-3 text-muted-foreground">{l.detail}</td>
                            <td className="py-1 pr-3 tabular-nums">{Math.round(l.ms)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </Block>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </section>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md border border-border bg-background p-3">
      <div className="text-lg font-semibold tabular-nums">{value}</div>
      <div className="text-xs text-muted-foreground">{label}</div>
    </div>
  );
}

function Block({
  icon: Icon,
  title,
  children,
}: {
  icon: typeof FlaskConical;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-2">
      <h3 className="flex items-center gap-2 text-sm font-semibold text-foreground/90">
        <Icon className="size-4 text-primary" /> {title}
      </h3>
      {children}
    </div>
  );
}

function SafetyTd({ note, reported }: { note: string; reported: boolean }) {
  return (
    <td className="py-1 pr-3">
      <span
        className={cn(
          "text-xs",
          reported ? "text-foreground/85" : "text-muted-foreground italic",
        )}
      >
        {note}
      </span>
    </td>
  );
}

"use client";

import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { AlertTriangle, Download, Loader2 } from "lucide-react";
import { AgentRail } from "@/components/report/agent-rail";
import { ComparisonTable } from "@/components/report/comparison-table";
import { TrialDataTable } from "@/components/report/trial-data-table";
import { EvidenceVisuals } from "@/components/report/evidence-visuals";
import { SectionCard } from "@/components/report/section-card";
import { CitationList } from "@/components/report/citation-list";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AGENTS } from "@/lib/placeholder-data";
import { mapAgents, mapReport, reportsApi } from "@/lib/api";
import type { AgentProgress, Report } from "@/types/report";

const EXPORTS = ["PDF", "PPTX", "Excel", "Markdown"] as const;

export function LiveReportStream({ id }: { id: string }) {
  const [report, setReport] = useState<Report | null>(null);
  const [agents, setAgents] = useState<AgentProgress[]>(() =>
    AGENTS.map((a) => ({ ...a })),
  );
  const [status, setStatus] = useState<Report["status"]>("queued");
  const [error, setError] = useState<string | null>(null);
  const esRef = useRef<EventSource | null>(null);

  const done = status === "complete";

  // Initial load + stream subscription.
  useEffect(() => {
    let active = true;

    (async () => {
      try {
        const raw = await reportsApi.getRaw(id);
        if (!active) return;
        setStatus(raw.status);
        if (raw.agents.length) setAgents(mapAgents(raw));
        if (raw.status === "complete") {
          setReport(mapReport(raw));
          return; // no need to stream a finished report
        }
        subscribe();
      } catch {
        if (active) setError("Could not load this report.");
      }
    })();

    function subscribe() {
      const es = new EventSource(reportsApi.streamUrl(id));
      esRef.current = es;

      es.addEventListener("status", (e) => {
        const d = JSON.parse((e as MessageEvent).data);
        setStatus(d.status);
      });
      es.addEventListener("agent", (e) => {
        const d = JSON.parse((e as MessageEvent).data);
        setAgents((prev) =>
          prev.map((a) =>
            a.key === d.agent ? { ...a, state: d.state, detail: d.detail } : a,
          ),
        );
      });
      es.addEventListener("complete", async () => {
        es.close();
        try {
          const full = await reportsApi.get(id);
          if (active) {
            setReport(full);
            setStatus("complete");
          }
        } catch {
          /* keep progress visible */
        }
      });
      es.addEventListener("error", (e) => {
        const msg = (e as MessageEvent).data;
        if (msg) {
          try {
            setError(JSON.parse(msg).message ?? "Pipeline error");
          } catch {
            setError("Pipeline error");
          }
          es.close();
        }
        // otherwise a transient connection error — EventSource auto-retries
      });
    }

    return () => {
      active = false;
      esRef.current?.close();
    };
  }, [id]);

  if (error) {
    return (
      <div className="mx-auto max-w-md py-20 text-center">
        <AlertTriangle className="mx-auto size-8 text-conf-verylow" />
        <p className="mt-3 text-sm text-muted-foreground">{error}</p>
      </div>
    );
  }

  const moleculeA = report?.moleculeA ?? "Molecule A";
  const moleculeB = report?.moleculeB ?? "Molecule B";
  const topic = report?.topic ?? "";

  return (
    <div className="space-y-8 py-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div className="space-y-1">
          <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
            {topic && <Badge>{topic}</Badge>}
            {!done ? (
              <span className="inline-flex items-center gap-1 text-primary">
                <Loader2 className="size-3.5 animate-spin" /> Generating…
              </span>
            ) : (
              <span className="text-conf-high">Complete</span>
            )}
          </div>
          <h1 className="text-3xl font-bold tracking-tight">
            <span className="text-primary">{moleculeA}</span>
            <span className="text-muted-foreground"> vs </span>
            <span className="text-accent">{moleculeB}</span>
          </h1>
        </div>
        <div className="flex flex-wrap gap-2">
          {EXPORTS.map((f) => (
            <Button key={f} variant="outline" size="sm" disabled={!done}>
              <Download className="size-4" />
              {f}
            </Button>
          ))}
        </div>
      </div>

      <div className="grid gap-8 lg:grid-cols-[260px_1fr]">
        <aside className="lg:sticky lg:top-20 lg:self-start">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Evidence pipeline
              </CardTitle>
            </CardHeader>
            <CardContent>
              <AgentRail agents={agents} />
            </CardContent>
          </Card>
        </aside>

        <div className="space-y-6">
          {report ? (
            <>
              <section className="space-y-3">
                <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                  Side-by-side comparison
                </h2>
                <ComparisonTable
                  rows={report.comparison}
                  moleculeA={moleculeA}
                  moleculeB={moleculeB}
                  citations={report.citations}
                />
              </section>
              <EvidenceVisuals
                moleculeA={moleculeA}
                moleculeB={moleculeB}
                citations={report.citations}
                comparison={report.comparison}
                moleculeEvidence={report.moleculeEvidence}
              />
              {report.extractions.length > 0 && (
                <section className="space-y-3">
                  <div>
                    <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                      Extracted trial data
                    </h2>
                    <p className="text-xs text-muted-foreground">
                      Retrieved evidence — structured fields pulled from each source
                      by the Trial-Extraction agent. Empty fields read “Not reported”.
                    </p>
                  </div>
                  <TrialDataTable extractions={report.extractions} />
                </section>
              )}
              <section className="space-y-4">
                <AnimatePresence>
                  {report.sections.map((section) => (
                    <motion.div
                      key={section.key}
                      layout
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                    >
                      <SectionCard section={section} citations={report.citations} />
                    </motion.div>
                  ))}
                </AnimatePresence>
              </section>
              <CitationList citations={report.citations} />
            </>
          ) : (
            <div className="grid place-items-center rounded-lg border border-dashed border-border py-24 text-center text-sm text-muted-foreground">
              <div className="space-y-2">
                <Loader2 className="mx-auto size-6 animate-spin text-primary" />
                <p>Retrieving evidence and synthesizing the report…</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

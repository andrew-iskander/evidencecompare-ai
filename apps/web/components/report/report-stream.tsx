"use client";

import { useEffect, useMemo, useState } from "react";
import { Download, Loader2, Database, Sparkles, Stethoscope } from "lucide-react";
import { AgentRail } from "@/components/report/agent-rail";
import { ComparisonTable } from "@/components/report/comparison-table";
import { TrialDataTable } from "@/components/report/trial-data-table";
import { EvidenceVisuals } from "@/components/report/evidence-visuals";
import { SectionCard } from "@/components/report/section-card";
import { CitationList } from "@/components/report/citation-list";
import {
  ConflictBanner,
  TransparencyLayer,
} from "@/components/report/transparency-layer";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AGENTS, SAMPLE_REPORT } from "@/lib/placeholder-data";
import type { AgentProgress } from "@/types/report";

const EXPORTS = ["PDF", "PPTX", "Excel", "Markdown"] as const;

export function ReportStream({
  moleculeA,
  moleculeB,
  topic,
}: {
  moleculeA: string;
  moleculeB: string;
  topic: string;
}) {
  const report = useMemo(
    () => ({ ...SAMPLE_REPORT, moleculeA, moleculeB, topic }),
    [moleculeA, moleculeB, topic],
  );

  const [agents, setAgents] = useState<AgentProgress[]>(() =>
    AGENTS.map((a) => ({ ...a })),
  );
  const [done, setDone] = useState(false);

  // Simulate the streaming pipeline (offline demo; real reports use live SSE).
  useEffect(() => {
    let i = 0;
    const timers: ReturnType<typeof setTimeout>[] = [];
    const step = () => {
      setAgents((prev) =>
        prev.map((a, idx) => {
          if (idx < i) return { ...a, state: "done" };
          if (idx === i) return { ...a, state: "running" };
          return { ...a, state: "pending" };
        }),
      );
      i += 1;
      if (i <= AGENTS.length) {
        timers.push(setTimeout(step, 650));
      } else {
        setAgents((prev) => prev.map((a) => ({ ...a, state: "done" })));
        setDone(true);
      }
    };
    timers.push(setTimeout(step, 300));
    return () => timers.forEach(clearTimeout);
  }, [report.sections.length]);

  return (
    <div className="space-y-8 py-8">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div className="space-y-1">
          <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
            <Badge>{topic}</Badge>
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
            <Button
              key={f}
              variant="outline"
              size="sm"
              disabled={!done}
              title={done ? `Export ${f}` : "Available when complete"}
            >
              <Download className="size-4" />
              {f}
            </Button>
          ))}
        </div>
      </div>

      <div className="grid gap-8 lg:grid-cols-[260px_1fr]">
        {/* Progress rail */}
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

        {/* Report body */}
        <div className="space-y-6">
          {!done ? (
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
              <p className="text-center text-sm text-muted-foreground">
                Synthesizing the evidence report…
              </p>
            </section>
          ) : (
            <>
              {/* Layer 1 — Clinical Summary */}
              <TransparencyLayer
                label="Clinical Summary"
                description="Concise, evidence-grounded takeaways. Derived by AI from the retrieved evidence below."
                icon={Stethoscope}
              >
                {report.sections
                  .filter((s) => s.layer === "clinical_summary")
                  .map((section) => (
                    <SectionCard
                      key={section.key}
                      section={section}
                      citations={report.citations}
                    />
                  ))}
              </TransparencyLayer>

              {/* Layer 2 — Retrieved Evidence */}
              <TransparencyLayer
                label="Retrieved Evidence"
                description="The raw facts retrieved from trusted sources — verified citations, extracted trial data, and evidence volume. No AI interpretation here."
                icon={Database}
              >
                <ConflictBanner conflicts={report.conflicts} />
                <div className="space-y-3">
                  <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                    Side-by-side comparison
                  </h3>
                  <ComparisonTable
                    rows={report.comparison}
                    moleculeA={moleculeA}
                    moleculeB={moleculeB}
                    citations={report.citations}
                  />
                </div>
                {report.extractions.length > 0 && (
                  <div className="space-y-3">
                    <div>
                      <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                        Extracted trial data
                      </h3>
                      <p className="text-xs text-muted-foreground">
                        Structured fields pulled from each source by the
                        Trial-Extraction agent. Empty fields read “Not reported”.
                      </p>
                    </div>
                    <TrialDataTable extractions={report.extractions} />
                  </div>
                )}
                <EvidenceVisuals
                  moleculeA={moleculeA}
                  moleculeB={moleculeB}
                  citations={report.citations}
                  comparison={report.comparison}
                  moleculeEvidence={report.moleculeEvidence}
                />
                <CitationList citations={report.citations} />
              </TransparencyLayer>

              {/* Layer 3 — AI Interpretation */}
              <TransparencyLayer
                label="AI Interpretation"
                description="AI-synthesized narrative over the retrieved evidence. Every claim links to its citations — this is not medical advice."
                icon={Sparkles}
              >
                {report.sections
                  .filter((s) => s.layer === "ai_interpretation")
                  .map((section) => (
                    <SectionCard
                      key={section.key}
                      section={section}
                      citations={report.citations}
                    />
                  ))}
              </TransparencyLayer>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

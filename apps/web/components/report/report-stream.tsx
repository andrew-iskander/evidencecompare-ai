"use client";

import { useEffect, useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Download, Loader2 } from "lucide-react";
import { AgentRail } from "@/components/report/agent-rail";
import { ComparisonTable } from "@/components/report/comparison-table";
import { EvidenceVisuals } from "@/components/report/evidence-visuals";
import { SectionCard } from "@/components/report/section-card";
import { CitationList } from "@/components/report/citation-list";
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
  const [revealed, setRevealed] = useState(0);
  const [done, setDone] = useState(false);

  // Simulate the streaming pipeline (Phase 1: real SSE lands in Phase 2/3).
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
      // reveal a section roughly in step with agents
      setRevealed(Math.min(report.sections.length, Math.max(0, i - 1)));
      i += 1;
      if (i <= AGENTS.length) {
        timers.push(setTimeout(step, 650));
      } else {
        setAgents((prev) => prev.map((a) => ({ ...a, state: "done" })));
        setRevealed(report.sections.length);
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

          {done && (
            <EvidenceVisuals
              moleculeA={moleculeA}
              moleculeB={moleculeB}
              citations={report.citations}
              comparison={report.comparison}
              moleculeEvidence={report.moleculeEvidence}
            />
          )}

          <section className="space-y-4">
            <AnimatePresence>
              {report.sections.slice(0, revealed).map((section) => (
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
            {!done && (
              <p className="text-center text-sm text-muted-foreground">
                Synthesizing remaining sections…
              </p>
            )}
          </section>

          {done && <CitationList citations={report.citations} />}
        </div>
      </div>
    </div>
  );
}

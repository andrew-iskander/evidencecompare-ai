"use client";

import { motion } from "framer-motion";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { EvidencePyramid } from "@/components/report/viz/evidence-pyramid";
import { EvidenceTimeline } from "@/components/report/viz/evidence-timeline";
import { ConfidenceHeatmap } from "@/components/report/viz/confidence-heatmap";
import { RiskBenefitMatrix } from "@/components/report/viz/risk-benefit-matrix";
import type { Citation, ComparisonRow, MoleculeEvidence } from "@/types/report";

/**
 * Evidence visualizations (Phase 5): evidence pyramid, timeline, confidence
 * heatmap, and risk-benefit matrix — all derived from the same verified evidence
 * the rest of the report cites.
 */
export function EvidenceVisuals({
  moleculeA,
  moleculeB,
  citations,
  comparison,
  moleculeEvidence,
}: {
  moleculeA: string;
  moleculeB: string;
  citations: Citation[];
  comparison: ComparisonRow[];
  moleculeEvidence?: MoleculeEvidence;
}) {
  return (
    <section className="space-y-3">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
        Evidence visualizations
      </h2>
      <div className="grid gap-4 lg:grid-cols-2">
        <Panel
          className="lg:col-span-2"
          title="Evidence timeline"
          description="When the verified evidence was published, by tier."
        >
          <EvidenceTimeline citations={citations} />
        </Panel>

        <Panel
          title="Evidence pyramid"
          description="Citations across the study-design hierarchy."
        >
          <EvidencePyramid citations={citations} />
        </Panel>

        <Panel
          title="Risk–benefit matrix"
          description="Per-molecule evidence coverage: efficacy vs safety."
        >
          <RiskBenefitMatrix
            moleculeA={moleculeA}
            moleculeB={moleculeB}
            evidence={moleculeEvidence}
          />
        </Panel>

        <Panel
          className="lg:col-span-2"
          title="Confidence heatmap"
          description="GRADE certainty across every comparison dimension."
        >
          <ConfidenceHeatmap rows={comparison} />
        </Panel>
      </div>
    </section>
  );
}

function Panel({
  title,
  description,
  className,
  children,
}: {
  title: string;
  description: string;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className={className}
    >
      <Card className="h-full">
        <CardHeader>
          <CardTitle className="text-base">{title}</CardTitle>
          <CardDescription>{description}</CardDescription>
        </CardHeader>
        <CardContent>{children}</CardContent>
      </Card>
    </motion.div>
  );
}

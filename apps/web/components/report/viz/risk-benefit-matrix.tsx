"use client";

import { motion } from "framer-motion";
import type { MoleculeEvidence } from "@/types/report";
import { TipLayer, useTip } from "@/components/report/viz/viz-tooltip";

/**
 * Risk–benefit matrix — each molecule placed by how much retrieved, verified
 * evidence supports it: efficacy (trials + meta-analyses) on X, safety
 * (labels / contraindications / interactions / special populations) on Y.
 *
 * A vs B is an *identity* encoding → categorical primary/accent, but always with
 * a distinct marker shape (circle vs diamond) and a direct label, so the pair is
 * never distinguished by colour alone. It is an evidence-coverage map, not a
 * clinical risk-benefit verdict.
 */
export function RiskBenefitMatrix({
  moleculeA,
  moleculeB,
  evidence,
}: {
  moleculeA: string;
  moleculeB: string;
  evidence?: MoleculeEvidence;
}) {
  const { tip, show, hide } = useTip();

  if (!evidence) {
    return (
      <p className="py-8 text-center text-sm text-muted-foreground">
        Per-molecule evidence positioning is available on generated reports.
      </p>
    );
  }

  const maxX = Math.max(1, evidence.a.efficacy, evidence.b.efficacy);
  const maxY = Math.max(1, evidence.a.safety, evidence.b.safety);

  // Keep marks (and their right-hand labels) clear of the plot edges.
  const pos = (eff: number, saf: number) => ({
    left: 10 + (eff / maxX) * 62,
    bottom: 12 + (saf / maxY) * 72,
  });
  const pa = pos(evidence.a.efficacy, evidence.a.safety);
  let pb = pos(evidence.b.efficacy, evidence.b.safety);
  // Nudge B if the two molecules land on the same point, so both stay legible.
  if (Math.abs(pa.left - pb.left) < 3 && Math.abs(pa.bottom - pb.bottom) < 3) {
    pb = { left: pb.left + 4, bottom: pb.bottom + 4 };
  }

  return (
    <figure className="space-y-3">
      <div className="flex gap-2">
        <div className="flex items-center">
          <span className="whitespace-nowrap text-xs text-muted-foreground [writing-mode:vertical-rl] [transform:rotate(180deg)]">
            Safety evidence (citations) →
          </span>
        </div>
        <div className="flex-1">
          <div className="relative aspect-[4/3] w-full rounded-md border border-border bg-muted/20">
            {/* quadrant guides */}
            <div className="absolute inset-y-0 left-1/2 w-px bg-border/60" />
            <div className="absolute inset-x-0 top-1/2 h-px bg-border/60" />

            <Mark
              shape="circle"
              color="var(--primary)"
              label={moleculeA}
              left={pa.left}
              bottom={pa.bottom}
              onMove={(e) =>
                show(e, <EvTip name={moleculeA} s={evidence.a} />)
              }
              onLeave={hide}
            />
            <Mark
              shape="diamond"
              color="var(--accent)"
              label={moleculeB}
              left={pb.left}
              bottom={pb.bottom}
              onMove={(e) =>
                show(e, <EvTip name={moleculeB} s={evidence.b} />)
              }
              onLeave={hide}
            />
          </div>
          <div className="mt-1 text-center text-xs text-muted-foreground">
            Efficacy evidence (citations) →
          </div>
        </div>
      </div>

      <div className="flex flex-wrap gap-x-4 gap-y-1.5">
        <LegendItem shape="circle" color="var(--primary)" label={moleculeA} />
        <LegendItem shape="diamond" color="var(--accent)" label={moleculeB} />
      </div>
      <figcaption className="text-xs text-muted-foreground">
        Position reflects the volume of retrieved, verified evidence per molecule —
        an evidence-coverage map, not a clinical risk-benefit verdict.
      </figcaption>
      <TipLayer tip={tip} />
    </figure>
  );
}

function Mark({
  shape,
  color,
  label,
  left,
  bottom,
  onMove,
  onLeave,
}: {
  shape: "circle" | "diamond";
  color: string;
  label: string;
  left: number;
  bottom: number;
  onMove: (e: React.MouseEvent) => void;
  onLeave: () => void;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4, ease: "backOut" }}
      className="absolute flex -translate-x-1/2 translate-y-1/2 items-center gap-1.5"
      style={{ left: `${left}%`, bottom: `${bottom}%` }}
      onMouseMove={onMove}
      onMouseLeave={onLeave}
    >
      <Glyph shape={shape} color={color} />
      <span className="whitespace-nowrap text-xs font-medium">{label}</span>
    </motion.div>
  );
}

function Glyph({ shape, color }: { shape: "circle" | "diamond"; color: string }) {
  return (
    <span
      className={`block size-3.5 ring-2 ring-card ${
        shape === "circle" ? "rounded-full" : "rotate-45 rounded-[2px]"
      }`}
      style={{ backgroundColor: color }}
    />
  );
}

function LegendItem({
  shape,
  color,
  label,
}: {
  shape: "circle" | "diamond";
  color: string;
  label: string;
}) {
  return (
    <span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground">
      <Glyph shape={shape} color={color} />
      {label}
    </span>
  );
}

function EvTip({
  name,
  s,
}: {
  name: string;
  s: { efficacy: number; safety: number; guideline: number };
}) {
  return (
    <span>
      <strong>{name}</strong>
      <br />
      Efficacy: {s.efficacy} · Safety: {s.safety} · Guideline: {s.guideline}
    </span>
  );
}

"use client";

import { motion } from "framer-motion";
import type { Citation, StudyDesign } from "@/types/report";
import { TIER_LABEL, TIER_ORDER, tierColor, tierOf } from "@/lib/viz";
import { TipLayer, useTip } from "@/components/report/viz/viz-tooltip";

/**
 * Evidence timeline — each verified, dated citation as a dot on a single year
 * axis, coloured by evidence tier. Dots stack within a year to avoid overlap.
 */
export function EvidenceTimeline({ citations }: { citations: Citation[] }) {
  const dated = citations.filter((c) => typeof c.year === "number");
  const { tip, show, hide } = useTip();

  if (!dated.length) {
    return (
      <p className="py-8 text-center text-sm text-muted-foreground">
        No dated citations to place on a timeline.
      </p>
    );
  }

  const years = dated.map((c) => c.year as number);
  const min = Math.min(...years);
  const max = Math.max(...years);
  const span = Math.max(1, max - min);

  // Assign a vertical lane per citation by stacking within its year bucket.
  const perYear = new Map<number, number>();
  const placed = [...dated]
    .sort((a, b) => (a.year as number) - (b.year as number))
    .map((c) => {
      const y = c.year as number;
      const lane = perYear.get(y) ?? 0;
      perYear.set(y, lane + 1);
      return { c, y, lane };
    });
  const maxLane = Math.max(...placed.map((p) => p.lane));

  const tiersPresent = TIER_ORDER.filter((t) =>
    dated.some((c) => tierOf(c) === t),
  );

  const ticks = axisTicks(min, max);

  return (
    <figure className="space-y-3">
      <div
        className="relative w-full"
        style={{ height: `${64 + maxLane * 26}px` }}
      >
        {placed.map(({ c, y, lane }, i) => {
          const left = ((y - min) / span) * 100;
          return (
            <motion.button
              key={c.id}
              type="button"
              initial={{ opacity: 0, scale: 0 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.3, delay: i * 0.03 }}
              className="absolute size-3.5 -translate-x-1/2 rounded-full ring-2 ring-card focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              style={{
                left: `${clamp(left, 2, 98)}%`,
                bottom: `${28 + lane * 26}px`,
                backgroundColor: tierColor(tierOf(c)),
              }}
              onMouseMove={(e) => show(e, <CiteTip c={c} />)}
              onMouseLeave={hide}
              onFocus={(e) =>
                show(
                  { clientX: rectMid(e.currentTarget).x, clientY: rectMid(e.currentTarget).y },
                  <CiteTip c={c} />,
                )
              }
              onBlur={hide}
              aria-label={`${TIER_LABEL[tierOf(c)]}, ${y}: ${c.title}`}
            />
          );
        })}

        {/* axis */}
        <div className="absolute inset-x-0 bottom-5 h-px bg-border" />
        {ticks.map((t) => (
          <div
            key={t}
            className="absolute bottom-0 -translate-x-1/2 text-center"
            style={{ left: `${clamp(((t - min) / span) * 100, 2, 98)}%` }}
          >
            <div className="mx-auto h-1.5 w-px bg-border" />
            <span className="text-[11px] text-muted-foreground tabular-nums">
              {t}
            </span>
          </div>
        ))}
      </div>

      <TierLegend tiers={tiersPresent} />
      <TipLayer tip={tip} />
    </figure>
  );
}

function CiteTip({ c }: { c: Citation }) {
  return (
    <span>
      <strong>{TIER_LABEL[tierOf(c)]}</strong> · {c.year} · {c.source.toUpperCase()}
      <br />
      {c.title}
    </span>
  );
}

export function TierLegend({ tiers }: { tiers: StudyDesign[] }) {
  return (
    <div className="flex flex-wrap gap-x-4 gap-y-1.5">
      {tiers.map((t) => (
        <span key={t} className="inline-flex items-center gap-1.5 text-xs text-muted-foreground">
          <span
            className="size-2.5 rounded-full"
            style={{ backgroundColor: tierColor(t) }}
          />
          {TIER_LABEL[t]}
        </span>
      ))}
    </div>
  );
}

function axisTicks(min: number, max: number): number[] {
  if (min === max) return [min];
  const span = max - min;
  const step = span <= 6 ? 1 : span <= 15 ? 3 : 5;
  const ticks: number[] = [];
  for (let y = min; y <= max; y += step) ticks.push(y);
  if (ticks[ticks.length - 1] !== max) ticks.push(max);
  return ticks;
}

function clamp(n: number, lo: number, hi: number): number {
  return Math.max(lo, Math.min(hi, n));
}

function rectMid(el: HTMLElement): { x: number; y: number } {
  const r = el.getBoundingClientRect();
  return { x: r.left + r.width / 2, y: r.top + r.height / 2 };
}

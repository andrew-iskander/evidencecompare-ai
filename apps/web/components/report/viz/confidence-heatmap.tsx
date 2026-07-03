"use client";

import type { ComparisonRow, Confidence } from "@/types/report";
import {
  CONFIDENCE_LABEL,
  CONFIDENCE_ORDER,
  confidenceColor,
} from "@/lib/viz";
import { TipLayer, useTip } from "@/components/report/viz/viz-tooltip";

/**
 * Confidence heatmap — GRADE certainty across every comparison dimension.
 * Confidence is a *status* encoding, so each cell always carries its label and
 * citation count; colour only reinforces. Hover reveals the rationale.
 */
export function ConfidenceHeatmap({ rows }: { rows: ComparisonRow[] }) {
  const { tip, show, hide } = useTip();
  if (!rows.length) {
    return (
      <p className="py-8 text-center text-sm text-muted-foreground">
        No comparison dimensions to summarize.
      </p>
    );
  }

  return (
    <figure className="space-y-3">
      <div className="space-y-1.5">
        {rows.map((row) => (
          <div
            key={row.attribute}
            className="grid grid-cols-[1fr_auto] items-stretch gap-2"
          >
            <span className="flex items-center text-xs text-muted-foreground">
              {row.attribute}
            </span>
            <Cell
              confidence={row.confidence}
              count={row.citationIds.length}
              onMove={(e) =>
                show(
                  e,
                  <span>
                    <strong>{CONFIDENCE_LABEL[row.confidence]} certainty</strong>
                    {row.rationale ? (
                      <>
                        <br />
                        {row.rationale}
                      </>
                    ) : null}
                  </span>,
                )
              }
              onLeave={hide}
            />
          </div>
        ))}
      </div>
      <ConfidenceLegend />
      <TipLayer tip={tip} />
    </figure>
  );
}

function Cell({
  confidence,
  count,
  onMove,
  onLeave,
}: {
  confidence: Confidence;
  count: number;
  onMove: (e: React.MouseEvent) => void;
  onLeave: () => void;
}) {
  const color = confidenceColor(confidence);
  // Colour lives on the border + swatch (identity); text stays in ink so it
  // always meets contrast (dataviz: text wears text tokens, never the mark hue).
  return (
    <div
      className="flex min-w-[132px] items-center justify-between gap-2 rounded-[4px] border-l-4 px-2.5 py-1.5 text-xs font-medium"
      style={{
        borderColor: color,
        backgroundColor: `color-mix(in oklch, ${color} 12%, transparent)`,
      }}
      onMouseMove={onMove}
      onMouseLeave={onLeave}
    >
      <span className="flex items-center gap-1.5 text-foreground">
        <span className="size-2 rounded-full" style={{ backgroundColor: color }} />
        {CONFIDENCE_LABEL[confidence]}
      </span>
      <span className="tabular-nums text-muted-foreground">
        {count} cite{count === 1 ? "" : "s"}
      </span>
    </div>
  );
}

export function ConfidenceLegend() {
  return (
    <div className="flex flex-wrap gap-x-4 gap-y-1.5">
      {CONFIDENCE_ORDER.map((c) => (
        <span
          key={c}
          className="inline-flex items-center gap-1.5 text-xs text-muted-foreground"
        >
          <span
            className="size-2.5 rounded-[3px]"
            style={{ backgroundColor: confidenceColor(c) }}
          />
          {CONFIDENCE_LABEL[c]}
        </span>
      ))}
    </div>
  );
}

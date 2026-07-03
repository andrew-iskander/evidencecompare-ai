"use client";

import { motion } from "framer-motion";
import type { Citation } from "@/types/report";
import { TIER_LABEL, tierColor, tierCounts } from "@/lib/viz";
import { TipLayer, useTip } from "@/components/report/viz/viz-tooltip";

/**
 * Evidence pyramid — distribution of the verified citations across the study-
 * design hierarchy (strongest at the top). Bar width encodes count (the data);
 * colour is the sequential tier ramp. Tier + count are always directly labelled.
 */
export function EvidencePyramid({ citations }: { citations: Citation[] }) {
  const rows = tierCounts(citations);
  const total = citations.length;
  const max = Math.max(1, ...rows.map((r) => r.count));
  const { tip, show, hide } = useTip();

  if (!rows.length) {
    return <Empty />;
  }

  return (
    <figure className="space-y-3">
      <div className="space-y-2">
        {rows.map((r, i) => {
          const pct = (r.count / max) * 100;
          const share = total ? Math.round((r.count / total) * 100) : 0;
          return (
            <div key={r.tier} className="flex items-center gap-3">
              <span className="w-28 shrink-0 text-right text-xs text-muted-foreground">
                {TIER_LABEL[r.tier]}
              </span>
              <div className="relative flex-1">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.max(pct, 6)}%` }}
                  transition={{ duration: 0.5, delay: i * 0.05, ease: "easeOut" }}
                  className="mx-auto h-7 rounded-[4px]"
                  style={{ backgroundColor: tierColor(r.tier) }}
                  onMouseMove={(e) =>
                    show(
                      e,
                      <span>
                        <strong>{TIER_LABEL[r.tier]}</strong>
                        <br />
                        {r.count} of {total} citations ({share}%)
                      </span>,
                    )
                  }
                  onMouseLeave={hide}
                />
              </div>
              <span className="w-6 shrink-0 text-sm font-semibold tabular-nums">
                {r.count}
              </span>
            </div>
          );
        })}
      </div>
      <figcaption className="text-xs text-muted-foreground">
        {total} verified citation{total === 1 ? "" : "s"} by evidence tier
        (strongest at top).
      </figcaption>
      <TipLayer tip={tip} />
    </figure>
  );
}

function Empty() {
  return (
    <p className="py-8 text-center text-sm text-muted-foreground">
      No verified citations to chart yet.
    </p>
  );
}

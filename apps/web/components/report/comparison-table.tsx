"use client";

import { Fragment, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ChevronRight } from "lucide-react";
import { ConfidenceBadge } from "@/components/report/confidence-badge";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { Citation, ComparisonRow } from "@/types/report";

export function ComparisonTable({
  rows,
  moleculeA,
  moleculeB,
  citations = [],
}: {
  rows: ComparisonRow[];
  moleculeA: string;
  moleculeB: string;
  citations?: Citation[];
}) {
  const [open, setOpen] = useState<Set<string>>(new Set());
  const index = new Map(citations.map((c, i) => [c.id, { c, n: i + 1 }]));

  const toggle = (attr: string) =>
    setOpen((prev) => {
      const next = new Set(prev);
      if (next.has(attr)) next.delete(attr);
      else next.add(attr);
      return next;
    });

  return (
    <Card className="overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[680px] border-collapse text-sm">
          <thead>
            <tr className="border-b border-border bg-muted/50 text-left">
              <th className="w-8 px-2 py-3" />
              <th className="px-4 py-3 font-medium text-muted-foreground">Attribute</th>
              <th className="px-4 py-3 font-semibold text-primary">{moleculeA}</th>
              <th className="px-4 py-3 font-semibold text-accent">{moleculeB}</th>
              <th className="px-4 py-3 font-medium text-muted-foreground">Confidence</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => {
              const isOpen = open.has(row.attribute);
              const cited = row.citationIds
                .map((id) => index.get(id))
                .filter((x): x is { c: Citation; n: number } => Boolean(x));
              return (
                <Fragment key={row.attribute}>
                  <tr
                    className="cursor-pointer border-b border-border/60 hover:bg-muted/30"
                    onClick={() => toggle(row.attribute)}
                  >
                    <td className="px-2 py-3 align-top text-muted-foreground">
                      <ChevronRight
                        className={`size-4 transition-transform ${isOpen ? "rotate-90" : ""}`}
                      />
                    </td>
                    <td className="px-4 py-3 align-top font-medium">{row.attribute}</td>
                    <td className="px-4 py-3 align-top text-foreground/90">{row.valueA}</td>
                    <td className="px-4 py-3 align-top text-foreground/90">{row.valueB}</td>
                    <td className="px-4 py-3 align-top">
                      <ConfidenceBadge level={row.confidence} />
                    </td>
                  </tr>
                  <AnimatePresence initial={false}>
                    {isOpen && (
                      <motion.tr
                        key={`${row.attribute}-detail`}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="border-b border-border/60 bg-muted/20"
                      >
                        <td />
                        <td colSpan={4} className="px-4 pb-4 pt-0">
                          <div className="space-y-2 text-sm">
                            {row.rationale && (
                              <p className="text-muted-foreground">
                                <span className="font-medium text-foreground">
                                  Why this confidence:{" "}
                                </span>
                                {row.rationale}
                              </p>
                            )}
                            <div className="flex flex-wrap items-center gap-1.5">
                              <span className="text-xs font-medium text-muted-foreground">
                                Supporting evidence:
                              </span>
                              {cited.length > 0 ? (
                                cited.map(({ c, n }) => (
                                  <Badge key={c.id} variant="outline" title={c.title}>
                                    [{n}] {c.source.toUpperCase()}
                                    {c.year ? ` ${c.year}` : ""}
                                  </Badge>
                                ))
                              ) : (
                                <Badge variant="muted" title="Not asserted as fact">
                                  no supporting citation
                                </Badge>
                              )}
                            </div>
                          </div>
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

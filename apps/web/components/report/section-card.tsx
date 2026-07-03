"use client";

import { motion } from "framer-motion";
import { Info } from "lucide-react";
import { ConfidenceBadge } from "@/components/report/confidence-badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { Citation, ReportSection } from "@/types/report";

export function SectionCard({
  section,
  citations,
}: {
  section: ReportSection;
  citations: Citation[];
}) {
  const byId = new Map(citations.map((c) => [c.id, c]));

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
    >
      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <CardTitle className="text-lg">{section.title}</CardTitle>
          <ConfidenceBadge level={section.confidence} />
        </CardHeader>
        <CardContent className="space-y-3">
          {section.insufficientEvidence && (
            <div className="flex items-start gap-2 rounded-md border border-conf-verylow/30 bg-conf-verylow/10 px-3 py-2 text-sm text-conf-verylow">
              <Info className="mt-0.5 size-4 shrink-0" />
              <span>
                Evidence is insufficient for a confident conclusion. Stated
                plainly rather than inferred.
              </span>
            </div>
          )}
          <ul className="space-y-3">
            {section.claims.map((claim, i) => (
              <li key={i} className="text-sm leading-relaxed">
                <span>{claim.text}</span>{" "}
                {claim.citationIds.length > 0 ? (
                  <span className="ml-1 inline-flex flex-wrap gap-1 align-middle">
                    {claim.citationIds.map((id) => {
                      const c = byId.get(id);
                      const n =
                        citations.findIndex((x) => x.id === id) + 1 || undefined;
                      return (
                        <Badge key={id} variant="outline" title={c?.title}>
                          [{n}]
                        </Badge>
                      );
                    })}
                  </span>
                ) : (
                  <Badge variant="muted" title="No supporting citation">
                    unsourced
                  </Badge>
                )}
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </motion.div>
  );
}

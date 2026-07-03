import { BadgeCheck, ExternalLink } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Citation } from "@/types/report";

function href(c: Citation): string | undefined {
  if (c.doi) return `https://doi.org/${c.doi}`;
  if (c.pmid) return `https://pubmed.ncbi.nlm.nih.gov/${c.pmid}/`;
  return undefined;
}

export function CitationList({ citations }: { citations: Citation[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">References</CardTitle>
      </CardHeader>
      <CardContent>
        <ol className="space-y-3">
          {citations.map((c, i) => {
            const url = href(c);
            return (
              <li key={c.id} className="flex gap-3 text-sm">
                <span className="mt-0.5 w-6 shrink-0 text-right text-muted-foreground">
                  {i + 1}.
                </span>
                <div className="space-y-1">
                  <p className="font-medium leading-snug">{c.title}</p>
                  <p className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                    <span className="uppercase tracking-wide">{c.source}</span>
                    {c.year && <span>· {c.year}</span>}
                    {c.pmid && <span>· PMID {c.pmid}</span>}
                    {c.doi && <span>· DOI {c.doi}</span>}
                    {c.verified && (
                      <span className="inline-flex items-center gap-1 text-conf-high">
                        <BadgeCheck className="size-3.5" /> verified
                      </span>
                    )}
                    {url && (
                      <a
                        href={url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-primary hover:underline"
                      >
                        <ExternalLink className="size-3.5" /> open
                      </a>
                    )}
                  </p>
                </div>
              </li>
            );
          })}
        </ol>
      </CardContent>
    </Card>
  );
}

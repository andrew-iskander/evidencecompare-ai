import { ReportEntry } from "@/components/report/report-entry";
import { SAMPLE_REPORT } from "@/lib/placeholder-data";

type SearchParams = { [key: string]: string | string[] | undefined };

function first(v: string | string[] | undefined): string | undefined {
  return Array.isArray(v) ? v[0] : v;
}

export default async function ReportPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<SearchParams>;
}) {
  const { id } = await params;
  const sp = await searchParams;

  // Query params are only used to label the /reports/demo sample view.
  const moleculeA = first(sp.a) ?? SAMPLE_REPORT.moleculeA;
  const moleculeB = first(sp.b) ?? SAMPLE_REPORT.moleculeB;
  const topic = first(sp.topic) ?? SAMPLE_REPORT.topic;

  return (
    <ReportEntry
      id={id}
      moleculeA={moleculeA}
      moleculeB={moleculeB}
      topic={topic}
    />
  );
}

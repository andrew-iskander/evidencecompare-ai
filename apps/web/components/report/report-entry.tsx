"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { useAuth } from "@/components/auth-provider";
import { ReportStream } from "@/components/report/report-stream";
import { LiveReportStream } from "@/components/report/live-report-stream";

export function ReportEntry({
  id,
  moleculeA,
  moleculeB,
  topic,
}: {
  id: string;
  moleculeA: string;
  moleculeB: string;
  topic: string;
}) {
  const router = useRouter();
  const { user, ready } = useAuth();

  const isDemo = id === "demo";

  useEffect(() => {
    if (!isDemo && ready && !user) {
      router.replace(`/login?next=/reports/${id}`);
    }
  }, [isDemo, ready, user, router, id]);

  // The sample report needs no backend or auth.
  if (isDemo) {
    return (
      <ReportStream moleculeA={moleculeA} moleculeB={moleculeB} topic={topic} />
    );
  }

  if (!ready || !user) {
    return (
      <div className="grid place-items-center py-24 text-muted-foreground">
        <Loader2 className="size-6 animate-spin" />
      </div>
    );
  }

  return <LiveReportStream id={id} />;
}

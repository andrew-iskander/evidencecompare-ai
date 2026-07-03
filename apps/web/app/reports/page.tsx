"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { FileText, Loader2, Plus, Trash2 } from "lucide-react";
import { useAuth } from "@/components/auth-provider";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { reportsApi, type ReportSummary } from "@/lib/api";

const STATUS_TONE: Record<string, string> = {
  complete: "text-conf-high",
  running: "text-primary",
  queued: "text-muted-foreground",
  failed: "text-conf-verylow",
};

export default function ReportsPage() {
  const router = useRouter();
  const { user, ready } = useAuth();
  const [reports, setReports] = useState<ReportSummary[] | null>(null);

  const load = useCallback(async () => {
    try {
      setReports(await reportsApi.list());
    } catch {
      setReports([]);
    }
  }, []);

  useEffect(() => {
    if (ready && !user) router.replace("/login?next=/reports");
    else if (ready && user) load();
  }, [ready, user, router, load]);

  async function remove(id: string) {
    await reportsApi.remove(id);
    setReports((prev) => prev?.filter((r) => r.id !== id) ?? null);
  }

  if (!ready || !user || reports === null) {
    return (
      <div className="grid place-items-center py-24 text-muted-foreground">
        <Loader2 className="size-6 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6 py-12">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">My reports</h1>
        <Link href="/compare" className={cn(buttonVariants({ size: "sm" }))}>
          <Plus className="size-4" />
          New comparison
        </Link>
      </div>

      {reports.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center gap-3 py-16 text-center">
            <FileText className="size-8 text-muted-foreground" />
            <p className="text-muted-foreground">No reports yet.</p>
            <Link href="/compare" className={cn(buttonVariants())}>
              Start your first comparison
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {reports.map((r) => (
            <Card key={r.id}>
              <CardContent className="flex items-center justify-between gap-4 p-4">
                <Link href={`/reports/${r.id}`} className="min-w-0 flex-1">
                  <p className="truncate font-medium">
                    <span className="text-primary">{r.molecule_a}</span>
                    <span className="text-muted-foreground"> vs </span>
                    <span className="text-accent">{r.molecule_b}</span>
                  </p>
                  <p className="truncate text-sm text-muted-foreground">{r.topic}</p>
                </Link>
                <Badge variant="muted" className={STATUS_TONE[r.status]}>
                  {r.status}
                </Badge>
                <Button
                  variant="ghost"
                  size="icon"
                  aria-label="Delete report"
                  onClick={() => remove(r.id)}
                >
                  <Trash2 className="size-4" />
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { CheckCircle2, Loader2, RefreshCw, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { reportsApi } from "@/lib/api";
import type { Freshness } from "@/types/report";

/**
 * Living-evidence controls: shows whether the report is up to date, lets the user
 * check for newer high-tier evidence, and manually refresh (re-run) the report.
 */
export function FreshnessBar({
  reportId,
  initial,
}: {
  reportId: string;
  initial: Freshness;
}) {
  const router = useRouter();
  const [freshness, setFreshness] = useState<Freshness>(initial);
  const [checking, setChecking] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [note, setNote] = useState<string | null>(null);

  async function check() {
    setChecking(true);
    setNote(null);
    try {
      const res = await reportsApi.checkUpdates(reportId);
      setFreshness(res.status);
      setNote(
        res.status === "update_available"
          ? `${res.newItems} newer high-tier stud${res.newItems === 1 ? "y" : "ies"} found — refresh to include ${res.newItems === 1 ? "it" : "them"}.`
          : "No newer evidence found. This report is current.",
      );
    } catch {
      setNote("Could not check for updates.");
    } finally {
      setChecking(false);
    }
  }

  async function refresh() {
    setRefreshing(true);
    try {
      const next = await reportsApi.refresh(reportId);
      router.push(`/reports/${next.id}`);
    } catch {
      setNote("Could not start a refresh.");
      setRefreshing(false);
    }
  }

  const badge =
    freshness === "update_available" ? (
      <Badge
        variant="outline"
        className="border-conf-moderate/40 text-conf-moderate"
      >
        <AlertCircle className="size-3.5" /> Update available
      </Badge>
    ) : freshness === "up_to_date" ? (
      <Badge variant="outline" className="border-conf-high/40 text-conf-high">
        <CheckCircle2 className="size-3.5" /> Up to date
      </Badge>
    ) : (
      <Badge variant="muted">Freshness unknown</Badge>
    );

  return (
    <div className="flex flex-col gap-2 rounded-lg border border-border bg-muted/20 p-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-center gap-2">
        {badge}
        {note && <span className="text-xs text-muted-foreground">{note}</span>}
      </div>
      <div className="flex gap-2">
        <Button variant="outline" size="sm" onClick={check} disabled={checking}>
          {checking ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            <RefreshCw className="size-4" />
          )}
          Check for updates
        </Button>
        <Button size="sm" onClick={refresh} disabled={refreshing}>
          {refreshing ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            <RefreshCw className="size-4" />
          )}
          Refresh evidence
        </Button>
      </div>
    </div>
  );
}

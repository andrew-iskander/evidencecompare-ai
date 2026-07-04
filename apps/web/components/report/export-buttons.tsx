"use client";

import { useState } from "react";
import { Download, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { reportsApi } from "@/lib/api";

const FORMATS = [
  { label: "PDF", fmt: "pdf" },
  { label: "PPTX", fmt: "pptx" },
  { label: "Excel", fmt: "xlsx" },
  { label: "Markdown", fmt: "markdown" },
] as const;

/**
 * Report download buttons. Each fetches the generated file from the API (with
 * auth) and saves it via the browser. When `reportId` is absent (e.g. the sample
 * demo), the buttons are disabled.
 */
export function ExportButtons({
  reportId,
  disabled,
}: {
  reportId?: string;
  disabled?: boolean;
}) {
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function go(fmt: (typeof FORMATS)[number]["fmt"]) {
    if (!reportId) return;
    setBusy(fmt);
    setError(null);
    try {
      await reportsApi.download(reportId, fmt);
    } catch {
      setError(`Could not export ${fmt.toUpperCase()}.`);
    } finally {
      setBusy(null);
    }
  }

  const off = disabled || !reportId;

  return (
    <div className="flex flex-col items-end gap-1">
      <div className="flex flex-wrap gap-2">
        {FORMATS.map(({ label, fmt }) => (
          <Button
            key={fmt}
            variant="outline"
            size="sm"
            disabled={off || busy !== null}
            title={off ? "Available once the report is complete" : `Download ${label}`}
            onClick={() => go(fmt)}
          >
            {busy === fmt ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <Download className="size-4" />
            )}
            {label}
          </Button>
        ))}
      </div>
      {error && <span className="text-xs text-conf-verylow">{error}</span>}
    </div>
  );
}

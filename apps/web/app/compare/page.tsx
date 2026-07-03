"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ArrowLeftRight, Beaker, Loader2, Sparkles } from "lucide-react";
import { useAuth } from "@/components/auth-provider";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError, reportsApi } from "@/lib/api";

const PRESETS = [
  { a: "Telmisartan", b: "Valsartan", topic: "Cardioprotection" },
  { a: "Empagliflozin", b: "Dapagliflozin", topic: "Renal outcomes" },
  { a: "Atorvastatin", b: "Rosuvastatin", topic: "LDL reduction" },
];

export default function ComparePage() {
  const router = useRouter();
  const { user, ready } = useAuth();
  const [a, setA] = useState("");
  const [b, setB] = useState("");
  const [topic, setTopic] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (ready && !user) router.replace("/login?next=/compare");
  }, [ready, user, router]);

  const valid = a.trim() && b.trim() && topic.trim();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!valid || busy) return;
    setBusy(true);
    setError(null);
    try {
      const report = await reportsApi.create(a.trim(), b.trim(), topic.trim());
      router.push(`/reports/${report.id}`);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Failed to start the report.",
      );
      setBusy(false);
    }
  }

  function swap() {
    setA(b);
    setB(a);
  }

  if (!ready || !user) {
    return (
      <div className="grid place-items-center py-24 text-muted-foreground">
        <Loader2 className="size-6 animate-spin" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl space-y-8 py-12 sm:py-16">
      <div className="space-y-2 text-center">
        <h1 className="text-3xl font-bold tracking-tight">New comparison</h1>
        <p className="text-muted-foreground">
          Enter two molecules and the clinical question to compare them on.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Beaker className="size-5 text-primary" />
            Comparison inputs
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={submit} className="space-y-5">
            <div className="grid items-end gap-3 sm:grid-cols-[1fr_auto_1fr]">
              <div className="space-y-2">
                <Label htmlFor="mol-a">Molecule A</Label>
                <Input
                  id="mol-a"
                  placeholder="e.g. Telmisartan"
                  value={a}
                  onChange={(e) => setA(e.target.value)}
                  autoComplete="off"
                />
              </div>
              <Button
                type="button"
                variant="outline"
                size="icon"
                onClick={swap}
                aria-label="Swap molecules"
                className="mb-0.5 hidden sm:inline-flex"
              >
                <ArrowLeftRight className="size-4" />
              </Button>
              <div className="space-y-2">
                <Label htmlFor="mol-b">Molecule B</Label>
                <Input
                  id="mol-b"
                  placeholder="e.g. Valsartan"
                  value={b}
                  onChange={(e) => setB(e.target.value)}
                  autoComplete="off"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="topic">Clinical topic</Label>
              <Input
                id="topic"
                placeholder="e.g. Cardioprotection"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                autoComplete="off"
              />
            </div>

            {error && (
              <p className="rounded-md border border-conf-verylow/30 bg-conf-verylow/10 px-3 py-2 text-sm text-conf-verylow">
                {error}
              </p>
            )}

            <Button type="submit" size="lg" className="w-full" disabled={!valid || busy}>
              {busy ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <Sparkles className="size-4" />
              )}
              Generate evidence report
            </Button>
          </form>

          <div className="mt-6 space-y-2">
            <p className="text-xs font-medium text-muted-foreground">Try an example</p>
            <div className="flex flex-wrap gap-2">
              {PRESETS.map((p) => (
                <button
                  key={p.topic}
                  type="button"
                  onClick={() => {
                    setA(p.a);
                    setB(p.b);
                    setTopic(p.topic);
                  }}
                  className="rounded-full border border-border bg-muted/40 px-3 py-1 text-xs transition-colors hover:bg-muted"
                >
                  {p.a} vs {p.b} · {p.topic}
                </button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

import Link from "next/link";
import {
  ArrowRight,
  ShieldCheck,
  FlaskConical,
  FileDown,
  Layers,
} from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

const FEATURES = [
  {
    icon: ShieldCheck,
    title: "Never fabricated",
    body: "Every claim is grounded in retrieved, verified evidence. Insufficient evidence is stated plainly, not invented.",
  },
  {
    icon: FlaskConical,
    title: "Trusted sources only",
    body: "PubMed, Europe PMC, Crossref, ClinicalTrials.gov, FDA, ESC, NICE, Cochrane and more.",
  },
  {
    icon: Layers,
    title: "Confidence-scored",
    body: "GRADE-inspired confidence on every comparison row and section, from study design to consistency.",
  },
  {
    icon: FileDown,
    title: "Export anywhere",
    body: "One click to PDF, PowerPoint, Excel, or Markdown — citations intact.",
  },
];

export default function HomePage() {
  return (
    <div className="space-y-24 py-12 sm:py-16">
      {/* Hero */}
      <section className="relative overflow-hidden rounded-3xl border border-border bg-grid px-6 py-20 text-center sm:px-12">
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-background" />
        <div className="relative mx-auto max-w-3xl space-y-6">
          <span className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1 text-xs font-medium text-muted-foreground">
            <ShieldCheck className="size-3.5 text-primary" />
            AI Medical Evidence Intelligence
          </span>
          <h1 className="text-balance text-4xl font-bold tracking-tight sm:text-6xl">
            Compare two molecules on
            <span className="text-primary"> evidence</span>, not opinion.
          </h1>
          <p className="text-balance text-lg text-muted-foreground">
            EvidenceCompare AI builds a fully-cited, confidence-scored
            head-to-head between any two pharmaceutical molecules for a clinical
            topic you define — using only trustworthy sources.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
            <Link
              href="/compare"
              className={cn(buttonVariants({ size: "lg" }), "group")}
            >
              Start a comparison
              <ArrowRight className="size-4 transition-transform group-hover:translate-x-0.5" />
            </Link>
            <Link
              href="/reports/demo"
              className={cn(buttonVariants({ variant: "outline", size: "lg" }))}
            >
              View sample report
            </Link>
          </div>
          <p className="pt-4 text-xs text-muted-foreground">
            Example — A: Telmisartan · B: Valsartan · Topic: Cardioprotection
          </p>
        </div>
      </section>

      {/* Features */}
      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {FEATURES.map((f) => (
          <Card key={f.title} className="h-full">
            <CardContent className="space-y-3 p-6">
              <span className="grid size-10 place-items-center rounded-lg bg-primary/15 text-primary">
                <f.icon className="size-5" />
              </span>
              <h3 className="font-semibold">{f.title}</h3>
              <p className="text-sm text-muted-foreground">{f.body}</p>
            </CardContent>
          </Card>
        ))}
      </section>

      {/* Disclaimer */}
      <section className="rounded-2xl border border-border bg-muted/40 px-6 py-6 text-center text-sm text-muted-foreground">
        Decision-support for clinicians and researchers. Not a diagnostic device
        and not a substitute for professional clinical judgment.
      </section>
    </div>
  );
}

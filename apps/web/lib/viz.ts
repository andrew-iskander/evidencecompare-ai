import type { Citation, Confidence, StudyDesign } from "@/types/report";

/**
 * Shared vocabulary for the evidence visualizations (Phase 5).
 *
 * Colour is assigned by the job it does (dataviz method):
 *  - Evidence tier is an *ordinal magnitude* → a single-hue sequential ramp
 *    (`--tier-*`, CVD-safe by construction, monotonic lightness per theme).
 *  - Confidence is a *status* → the reserved `--conf-*` traffic-light hues,
 *    always shipped with a text label (never colour alone).
 *  - Molecule A vs B is *identity* → the categorical primary/accent pair, always
 *    paired with a distinct marker shape + direct label as secondary encoding.
 */

export const TIER_ORDER: StudyDesign[] = [
  "meta_analysis",
  "systematic_review",
  "guideline",
  "rct",
  "trial_registry",
  "drug_label",
  "other",
];

export const TIER_LABEL: Record<StudyDesign, string> = {
  meta_analysis: "Meta-analysis",
  systematic_review: "Systematic review",
  guideline: "Guideline",
  rct: "Randomized trial",
  trial_registry: "Registered trial",
  drug_label: "Drug label",
  other: "Other source",
};

/** CSS variable carrying the sequential colour for a tier (theme-aware).
 * Uses the base `--tier-*` custom properties (emitted to :root); the Tailwind
 * `@theme inline` `--color-*` names are NOT on :root, so they can't be used in
 * inline styles. */
export function tierColor(t: StudyDesign): string {
  return `var(--tier-${t})`;
}

export function tierOf(c: Citation): StudyDesign {
  return c.studyDesign ?? "other";
}

export const CONFIDENCE_ORDER: Confidence[] = [
  "high",
  "moderate",
  "low",
  "very_low",
];

export const CONFIDENCE_LABEL: Record<Confidence, string> = {
  high: "High",
  moderate: "Moderate",
  low: "Low",
  very_low: "Very low",
};

export function confidenceColor(c: Confidence): string {
  return c === "very_low" ? "var(--conf-verylow)" : `var(--conf-${c})`;
}

/** Numeric weight for a confidence level, used to position risk-benefit marks. */
export const CONFIDENCE_WEIGHT: Record<Confidence, number> = {
  high: 1,
  moderate: 0.66,
  low: 0.33,
  very_low: 0.1,
};

/** Extract the leading integer from an engine value like "3 item(s); …". */
export function leadingCount(value: string): number {
  const m = value.match(/^\s*(\d+)/);
  return m ? Number(m[1]) : 0;
}

/** Group citations by evidence tier, in hierarchy order. */
export function tierCounts(citations: Citation[]): { tier: StudyDesign; count: number }[] {
  const counts = new Map<StudyDesign, number>();
  for (const c of citations) {
    const t = tierOf(c);
    counts.set(t, (counts.get(t) ?? 0) + 1);
  }
  return TIER_ORDER.map((tier) => ({ tier, count: counts.get(tier) ?? 0 })).filter(
    (r) => r.count > 0,
  );
}

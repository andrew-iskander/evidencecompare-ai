/**
 * Frontend report types. In production these are generated from the backend
 * OpenAPI schema (packages/shared-types). Kept hand-written for Phase 1 so the
 * UI can be built against placeholder data before the API exists.
 */

export type Confidence = "high" | "moderate" | "low" | "very_low";

export type ReportStatus = "queued" | "running" | "complete" | "failed";

export type Freshness = "up_to_date" | "update_available" | "unknown";

export type AgentKey =
  | "interpreter"
  | "search"
  | "guideline"
  | "extraction"
  | "ranking"
  | "safety"
  | "conflict"
  | "verification"
  | "writer"
  | "visualization"
  | "report"
  | "monitor"
  // legacy V2 key, kept so old reports still map cleanly
  | "comparison";

export type AgentState = "pending" | "running" | "done" | "error";

export interface AgentProgress {
  key: AgentKey;
  label: string;
  state: AgentState;
  detail?: string;
}

export type StudyDesign =
  | "meta_analysis"
  | "systematic_review"
  | "guideline"
  | "rct"
  | "trial_registry"
  | "drug_label"
  | "other";

export interface Citation {
  id: string;
  title: string;
  source: string; // pubmed | crossref | ctgov | esc | ...
  studyDesign?: StudyDesign;
  doi?: string;
  pmid?: string;
  year?: number;
  verified: boolean;
}

export interface Claim {
  text: string;
  citationIds: string[];
}

export type SectionKey =
  | "executive_summary"
  | "clinical_pearls"
  | "mechanism_of_action"
  | "guidelines"
  | "trials"
  | "meta_analyses"
  | "systematic_reviews"
  | "safety"
  | "contraindications"
  | "interactions"
  | "special_populations"
  | "evidence_ranking"
  | "limitations"
  | "research_gaps"
  | "evidence_gaps";

/** AI-transparency layer a section belongs to. */
export type TransparencyLayerKey =
  | "retrieved_evidence"
  | "ai_interpretation"
  | "clinical_summary";

export interface ReportSection {
  key: SectionKey;
  title: string;
  layer: TransparencyLayerKey;
  confidence: Confidence;
  insufficientEvidence?: boolean;
  claims: Claim[];
}

export interface ComparisonRow {
  attribute: string;
  valueA: string;
  valueB: string;
  confidence: Confidence;
  rationale?: string;
  citationIds: string[];
}

/** Structured data extracted from one study by the Trial-Extraction agent. */
export interface TrialExtraction {
  refKey: string;
  title: string;
  studyDesign?: StudyDesign;
  population?: string;
  intervention?: string;
  comparator?: string;
  sampleSize?: number;
  outcomes: string[];
  hazardRatio?: string;
  relativeRisk?: string;
  confidenceInterval?: string;
  pValue?: string;
  adverseEvents: string[];
  strengths: string[];
  limitations: string[];
  extractorModel?: string;
}

export interface MoleculeEvidenceSide {
  efficacy: number;
  safety: number;
  guideline: number;
}

export interface MoleculeEvidence {
  a: MoleculeEvidenceSide;
  b: MoleculeEvidenceSide;
}

/**
 * V3 multi-agent artifacts. These are passed through from the backend in their
 * native (snake_case) JSON shape and rendered by the Research-Process panel; they
 * are optional so legacy V2 reports (which lack them) still map cleanly.
 */
export interface AgentLogEntry {
  agent: string;
  label: string;
  model?: string | null;
  state: string;
  detail: string;
  cost_usd: number;
  input_tokens: number;
  output_tokens: number;
  ms: number;
}

export interface ResearchProcess {
  logs: AgentLogEntry[];
  timings: Record<string, number>;
  snapshot: Record<string, unknown>;
  verification?: {
    checked: number;
    verified: number;
    removed: number;
    broken: Array<Record<string, unknown>>;
  } | null;
}

export interface EvidenceScores {
  overall: Record<string, number | string | Record<string, number>>;
  studies: Array<Record<string, number | string | null>>;
}

export interface SafetyCell {
  status: "reported" | "not_reported";
  citation_ids: string[];
  note: string;
}

export interface SafetyMatrix {
  molecule_a: string;
  molecule_b: string;
  rows: Array<{ key: string; label: string; a: SafetyCell; b: SafetyCell }>;
}

export interface Reconciliation {
  has_conflict: boolean;
  notes: string[];
  explanations: Array<{ molecule: string; axes: string[]; text: string }>;
  summary: string;
  consistency_score?: number | null;
}

export interface Report {
  id: string;
  status: ReportStatus;
  moleculeA: string;
  moleculeB: string;
  topic: string;
  sections: ReportSection[];
  comparison: ComparisonRow[];
  citations: Citation[];
  extractions: TrialExtraction[];
  moleculeEvidence?: MoleculeEvidence;
  costUsd?: number;
  freshness: Freshness;
  freshnessCheckedAt?: string;
  cached?: boolean;
  conflicts: string[];
  // V3 multi-agent artifacts (optional; present on V3 reports).
  scores?: EvidenceScores;
  safetyMatrix?: SafetyMatrix;
  reconciliation?: Reconciliation;
  researchProcess?: ResearchProcess;
}

/** Result of a living-evidence check. */
export interface FreshnessResult {
  status: Freshness;
  newItems: number;
  checkedAt?: string;
  details: string[];
}

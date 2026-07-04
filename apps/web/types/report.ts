/**
 * Frontend report types. In production these are generated from the backend
 * OpenAPI schema (packages/shared-types). Kept hand-written for Phase 1 so the
 * UI can be built against placeholder data before the API exists.
 */

export type Confidence = "high" | "moderate" | "low" | "very_low";

export type ReportStatus = "queued" | "running" | "complete" | "failed";

export type Freshness = "up_to_date" | "update_available" | "unknown";

export type AgentKey =
  | "search"
  | "ranking"
  | "extraction"
  | "guideline"
  | "comparison"
  | "writer";

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
  | "limitations"
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
}

/** Result of a living-evidence check. */
export interface FreshnessResult {
  status: Freshness;
  newItems: number;
  checkedAt?: string;
  details: string[];
}

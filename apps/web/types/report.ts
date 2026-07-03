/**
 * Frontend report types. In production these are generated from the backend
 * OpenAPI schema (packages/shared-types). Kept hand-written for Phase 1 so the
 * UI can be built against placeholder data before the API exists.
 */

export type Confidence = "high" | "moderate" | "low" | "very_low";

export type ReportStatus = "queued" | "running" | "complete" | "failed";

export type AgentKey =
  | "search"
  | "guideline"
  | "trial"
  | "meta_analysis"
  | "safety"
  | "ranking"
  | "verification"
  | "report";

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

export interface ReportSection {
  key: SectionKey;
  title: string;
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
  moleculeEvidence?: MoleculeEvidence;
  costUsd?: number;
}

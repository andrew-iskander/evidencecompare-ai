import type {
  AgentProgress,
  Citation,
  ComparisonRow,
  Freshness,
  FreshnessResult,
  Report,
  ReportSection,
  TrialExtraction,
} from "@/types/report";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

// ---- Token storage ----
const ACCESS = "ec_access";
const REFRESH = "ec_refresh";

export const tokens = {
  access: (): string | null =>
    typeof window === "undefined" ? null : localStorage.getItem(ACCESS),
  refresh: (): string | null =>
    typeof window === "undefined" ? null : localStorage.getItem(REFRESH),
  set(access: string, refresh?: string) {
    if (typeof window === "undefined") return;
    localStorage.setItem(ACCESS, access);
    if (refresh) localStorage.setItem(REFRESH, refresh);
  },
  clear() {
    if (typeof window === "undefined") return;
    localStorage.removeItem(ACCESS);
    localStorage.removeItem(REFRESH);
  },
};

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function parseError(res: Response): Promise<string> {
  try {
    const body = await res.json();
    return body?.detail ?? body?.error?.message ?? res.statusText;
  } catch {
    return res.statusText;
  }
}

async function refreshAccess(): Promise<boolean> {
  const refresh = tokens.refresh();
  if (!refresh) return false;
  const res = await fetch(`${API_BASE}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refresh }),
  });
  if (!res.ok) return false;
  const data = await res.json();
  tokens.set(data.access_token);
  return true;
}

async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  retry = true,
): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const access = tokens.access();
  if (access) headers.set("Authorization", `Bearer ${access}`);

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (res.status === 401 && retry && (await refreshAccess())) {
    return apiFetch<T>(path, options, false);
  }
  if (!res.ok) throw new ApiError(res.status, await parseError(res));
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

// ---- Auth ----
export interface UserOut {
  id: string;
  email: string;
  role: string;
}

export const authApi = {
  async register(email: string, password: string): Promise<UserOut> {
    return apiFetch<UserOut>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  },
  async login(email: string, password: string): Promise<void> {
    const data = await apiFetch<{ access_token: string; refresh_token: string }>(
      "/auth/login",
      { method: "POST", body: JSON.stringify({ email, password }) },
      false,
    );
    tokens.set(data.access_token, data.refresh_token);
  },
  async me(): Promise<UserOut> {
    return apiFetch<UserOut>("/auth/me");
  },
  logout() {
    tokens.clear();
  },
};

// ---- Report mapping (backend snake_case -> frontend camelCase) ----
interface RawClaim {
  text: string;
  citation_ids: string[];
}
interface RawSection {
  section_key: string;
  title: string;
  layer: ReportSection["layer"];
  confidence: ReportSection["confidence"];
  insufficient_evidence: boolean;
  claims: RawClaim[];
}
interface RawRow {
  attribute: string;
  value_a: string;
  value_b: string;
  confidence: ComparisonRow["confidence"];
  rationale: string | null;
  citation_ids: string[];
}
interface RawCitation {
  ref_key: string;
  title: string;
  source: string;
  study_design: string | null;
  doi: string | null;
  pmid: string | null;
  year: number | null;
  verified: boolean;
}
interface RawExtraction {
  ref_key: string;
  title: string;
  study_design: string | null;
  population: string | null;
  intervention: string | null;
  comparator: string | null;
  sample_size: number | null;
  outcomes: string[];
  hazard_ratio: string | null;
  relative_risk: string | null;
  confidence_interval: string | null;
  p_value: string | null;
  adverse_events: string[];
  strengths: string[];
  limitations: string[];
  extractor_model: string | null;
}
interface RawAgent {
  agent: string;
  label: string;
  state: AgentProgress["state"];
  detail: string | null;
}
interface RawMoleculeEvidence {
  a: { efficacy: number; safety: number; guideline: number };
  b: { efficacy: number; safety: number; guideline: number };
}
export interface RawReport {
  id: string;
  status: Report["status"];
  molecule_a: string;
  molecule_b: string;
  topic: string;
  model_synthesis: string | null;
  cost_usd: number;
  freshness: Freshness;
  freshness_checked_at: string | null;
  cached: boolean;
  conflicts: string[];
  sections: RawSection[];
  comparison: RawRow[];
  citations: RawCitation[];
  extractions: RawExtraction[];
  agents: RawAgent[];
  molecule_evidence: RawMoleculeEvidence | null;
}

export function mapReport(raw: RawReport): Report {
  return {
    id: raw.id,
    status: raw.status,
    moleculeA: raw.molecule_a,
    moleculeB: raw.molecule_b,
    topic: raw.topic,
    costUsd: raw.cost_usd,
    sections: raw.sections.map(
      (s): ReportSection => ({
        key: s.section_key as ReportSection["key"],
        title: s.title,
        layer: s.layer ?? "ai_interpretation",
        confidence: s.confidence,
        insufficientEvidence: s.insufficient_evidence,
        claims: s.claims.map((c) => ({ text: c.text, citationIds: c.citation_ids })),
      }),
    ),
    comparison: raw.comparison.map(
      (r): ComparisonRow => ({
        attribute: r.attribute,
        valueA: r.value_a,
        valueB: r.value_b,
        confidence: r.confidence,
        rationale: r.rationale ?? undefined,
        citationIds: r.citation_ids,
      }),
    ),
    citations: raw.citations.map(
      (c): Citation => ({
        id: c.ref_key,
        title: c.title,
        source: c.source,
        studyDesign: (c.study_design as Citation["studyDesign"]) ?? undefined,
        doi: c.doi ?? undefined,
        pmid: c.pmid ?? undefined,
        year: c.year ?? undefined,
        verified: c.verified,
      }),
    ),
    extractions: (raw.extractions ?? []).map(
      (e): TrialExtraction => ({
        refKey: e.ref_key,
        title: e.title,
        studyDesign: (e.study_design as TrialExtraction["studyDesign"]) ?? undefined,
        population: e.population ?? undefined,
        intervention: e.intervention ?? undefined,
        comparator: e.comparator ?? undefined,
        sampleSize: e.sample_size ?? undefined,
        outcomes: e.outcomes ?? [],
        hazardRatio: e.hazard_ratio ?? undefined,
        relativeRisk: e.relative_risk ?? undefined,
        confidenceInterval: e.confidence_interval ?? undefined,
        pValue: e.p_value ?? undefined,
        adverseEvents: e.adverse_events ?? [],
        strengths: e.strengths ?? [],
        limitations: e.limitations ?? [],
        extractorModel: e.extractor_model ?? undefined,
      }),
    ),
    moleculeEvidence: raw.molecule_evidence ?? undefined,
    freshness: raw.freshness ?? "unknown",
    freshnessCheckedAt: raw.freshness_checked_at ?? undefined,
    cached: raw.cached ?? false,
    conflicts: raw.conflicts ?? [],
  };
}

export function mapAgents(raw: RawReport): AgentProgress[] {
  return raw.agents.map((a) => ({
    key: a.agent as AgentProgress["key"],
    label: a.label,
    state: a.state,
    detail: a.detail ?? undefined,
  }));
}

export interface ReportSummary {
  id: string;
  molecule_a: string;
  molecule_b: string;
  topic: string;
  status: Report["status"];
  created_at: string;
  completed_at: string | null;
}

export const reportsApi = {
  async create(
    moleculeA: string,
    moleculeB: string,
    topic: string,
  ): Promise<Report> {
    const raw = await apiFetch<RawReport>("/reports", {
      method: "POST",
      body: JSON.stringify({
        molecule_a: moleculeA,
        molecule_b: moleculeB,
        topic,
      }),
    });
    return mapReport(raw);
  },
  async getRaw(id: string): Promise<RawReport> {
    return apiFetch<RawReport>(`/reports/${id}`);
  },
  async get(id: string): Promise<Report> {
    return mapReport(await this.getRaw(id));
  },
  async list(): Promise<ReportSummary[]> {
    return apiFetch<ReportSummary[]>("/reports");
  },
  // Manual refresh: run a fresh evidence report from the same inputs.
  async refresh(id: string): Promise<Report> {
    const raw = await apiFetch<RawReport>(`/reports/${id}/refresh`, {
      method: "POST",
    });
    return mapReport(raw);
  },
  // Living evidence: ask the backend to look for newer high-tier evidence.
  async checkUpdates(id: string): Promise<FreshnessResult> {
    const raw = await apiFetch<{
      status: Freshness;
      new_items: number;
      checked_at: string | null;
      details: string[];
    }>(`/reports/${id}/check-updates`, { method: "POST" });
    return {
      status: raw.status,
      newItems: raw.new_items,
      checkedAt: raw.checked_at ?? undefined,
      details: raw.details,
    };
  },
  async remove(id: string): Promise<void> {
    await apiFetch<void>(`/reports/${id}`, { method: "DELETE" });
  },
  // Download a report as pdf | pptx | xlsx | markdown (fetch with auth → save blob).
  async download(
    id: string,
    format: "pdf" | "pptx" | "xlsx" | "markdown",
  ): Promise<void> {
    const access = tokens.access();
    const res = await fetch(`${API_BASE}/reports/${id}/download?format=${format}`, {
      headers: access ? { Authorization: `Bearer ${access}` } : {},
    });
    if (!res.ok) throw new ApiError(res.status, await parseError(res));
    const blob = await res.blob();
    const cd = res.headers.get("Content-Disposition") ?? "";
    const match = /filename="?([^"]+)"?/.exec(cd);
    const filename = match?.[1] ?? `report.${format === "markdown" ? "md" : format}`;
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  },
  streamUrl(id: string): string {
    const token = tokens.access() ?? "";
    return `${API_BASE}/reports/${id}/stream?token=${encodeURIComponent(token)}`;
  },
};

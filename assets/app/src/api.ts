export interface Health {
  ok: boolean;
  hydradb: string;
}

export interface Example {
  question: string;
  hint: string;
  tag?: string;
}

export interface ProjectSummary {
  id: string;
  repo: string;
  url: string;
  demo: boolean;
  generated_at: number;
  stats: {
    nodes: number;
    versions: number;
    services: number;
    malicious: number;
    advisories: number;
    edges: number;
  };
  advisory_count: number;
}

export interface Session {
  id: string;
  title: string;
  created_at: number;
  turns: SessionTurn[];
}

export interface ProjectOverview {
  project: { id: string; repo: string; url: string; demo: boolean };
  dataset: string;
  stats: {
    nodes: number;
    versions: number;
    services: number;
    malicious: number;
    advisories: number;
    edges: number;
  };
  advisories: Array<{ name: string; version: string; advisory_id: string }>;
  examples: Example[];
  sessions: Session[];
}

export interface Overview {
  dataset: string;
  nodes: Record<string, number>;
  total_nodes: number;
  malicious_versions: number;
  typosquat_versions: number;
  advisories: number;
  exposures: Array<{
    name: string;
    version: string;
    advisory_id: string;
    services: string[];
  }>;
  examples: Example[];
}

export interface EvidenceStep {
  purpose: string;
  cypher: string;
  params: Record<string, unknown> | null;
  row_count: number;
  elapsed_ms: number;
}

export interface Payload {
  found?: boolean;
  node_id?: number;
  name?: string | null;
  version?: string | null;
  services?: string[];
  paths?: Array<{
    service: string;
    app?: string | null;
    name?: string | null;
    version?: string | null;
    resolved_at?: string | null;
    flag?: boolean;
  }>;
  lockfiles?: Array<{
    app: string;
    service: string;
    name: string;
    version: string;
    resolved_at: string;
  }>;
  recompute_agrees?: boolean;
  contradictions?: string[];
  dependant_count?: number;
  levels?: Array<Array<{ id: number; name: string; version: string }>>;
  developer?: string | null;
  packages?: string[];
  seeds?: string[];
  candidates?: Array<{
    id: number;
    name: string;
    nearest_seed?: string | null;
    score?: number;
    in_degree?: number;
    deprecated?: boolean;
  }>;
  node?: Record<string, unknown>;
}

export interface AskResponse {
  question: string;
  intent: string;
  answer: string;
  summary: string;
  abstain: boolean;
  reason: string;
  healed: boolean;
  reported: boolean;
  latency_ms: number;
  query_count: number;
  evidence_chain: EvidenceStep[];
  payload: Payload;
  server_ms: number;
}

export interface SubgraphResponse {
  node_id: number;
  nodes: Array<{ id: number; name?: string | null; version?: string | null; via?: string | null }>;
  edges: Array<{ src: number; dst: number; type: string }>;
  elapsed_ms: number;
}

export interface ExposureReport {
  generated_ms: number;
  advisories_checked: number;
  advisories_present: number;
  exposures: Array<{
    advisory_id: string;
    name: string;
    version: string;
    services: string[];
    lockfile_count: number;
    appearing: string[];
    resolved_while_live: Array<{
      app: string;
      service: string;
      name: string;
      version: string;
      resolved_at: number;
    }>;
    recompute_agrees: boolean;
    query_count: number;
  }>;
  totals: {
    services_exposed: number;
    apps_at_risk: number;
    live_resolutions: number;
  };
}

export interface SessionTurn {
  answer: AskResponse;
  graph?: SubgraphResponse;
  t: number;
}

export interface Customer {
  id: number;
  question: string;
  turns: SessionTurn[];
}

async function json<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.error ?? detail;
    } catch {
      /* keep statusText */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => json<Health>("/api/health"),
  overview: () => json<Overview>("/api/overview"),
  ask: (question: string, llmKey?: string) =>
    json<AskResponse>("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, llm_key: llmKey }),
    }),
  subgraph: (name: string, version: string) =>
    json<SubgraphResponse>("/api/subgraph", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, version }),
    }),
  report: () => json<ExposureReport>("/api/report"),
  projects: () => json<{ projects: ProjectSummary[] }>("/api/projects"),
  addProject: (url: string) =>
    json<{ id: string; repo: string; stats: object }>("/api/projects", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    }),
  projectOverview: (id: string) => json<ProjectOverview>(`/api/projects/${encodeURIComponent(id)}`),
  newSession: (id: string) =>
    json<Session>(`/api/projects/${encodeURIComponent(id)}/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    }),
  projectAsk: (id: string, question: string, sessionId: string | null, llmKey?: string) =>
    json<AskResponse>(`/api/projects/${encodeURIComponent(id)}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, session_id: sessionId, llm_key: llmKey }),
    }),
  projectScan: (id: string) =>
    json<ExposureReport>(`/api/projects/${encodeURIComponent(id)}/scan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    }),
  keyCheck: (key: string) =>
    json<{ ok: boolean }>("/api/keycheck", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ llm_key: key }),
    }),
};

export function nodeKey(name?: string | null, version?: string | null): string {
  return `${name ?? "?"}@${version ?? "?"}`;
}
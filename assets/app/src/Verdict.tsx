import { useState } from "react";
import type { AskResponse, EvidenceStep, Payload } from "./api";
import { ChevronDown, ChevronRight, Eye, ShieldAlert, Split, TerminalSquare, TrendingUp } from "lucide-react";

export const INTENT_TAG: Record<string, string> = {
  EXPOSED_SERVICES: "exposed",
  RESOLVED_WHILE_LIVE: "resolved",
  MAINTAINER_CONTAGION: "contagion",
  TYPOSQUAT_CANDIDATES: "typosquat",
  BLAST_RADIUS: "blast",
  PACKAGE_LOOKUP: "lookup",
  UNSUPPORTED: "abstain",
};

function EvidenceChain({ chain }: { chain: EvidenceStep[] }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="evidence">
      <button className="ev-toggle" onClick={() => setOpen((o) => !o)}>
        {open ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
        evidence chain · {chain.length} quer{chain.length === 1 ? "y" : "ies"} ·{" "}
        {chain.reduce((n, e) => n + e.row_count, 0).toLocaleString()} rows examined
      </button>
      {open && (
        <div className="ev-body">
          {chain.map((e, i) => (
            <div className="ev-step" key={i}>
              <div className="purpose">
                {i + 1}. {e.purpose}
              </div>
              <div className="rowmeta">
                {e.row_count} rows · {e.elapsed_ms.toFixed(1)}ms
              </div>
              <pre>
                {e.cypher}
                {e.params && Object.keys(e.params).length > 0
                  ? `\n-- params ${JSON.stringify(e.params)}`
                  : ""}
              </pre>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function Exposed({ p }: { p: Payload }) {
  return (
    <>
      <div className="services-row">
        {(p.services ?? []).map((s) => (
          <span className="service" key={s}>
            {s}
          </span>
        ))}
      </div>
      {p.paths && p.paths.length > 0 && (
        <div className="paths">
          <div className="head">
            <span>service</span>
            <span>app</span>
            <span>version</span>
            <span>resolved</span>
            <span>flag</span>
          </div>
          {p.paths.map((r, i) => (
            <div className={`row ${r.flag ? "bad" : ""}`} key={i}>
              <span>{r.service}</span>
              <span>{r.app ?? "—"}</span>
              <span>
                {r.name}@{r.version}
              </span>
              <span>{r.resolved_at ?? "—"}</span>
              <span>{r.flag ? <span className="warn-pill">LOW</span> : "—"}</span>
            </div>
          ))}
        </div>
      )}
    </>
  );
}

function Resolved({ p }: { p: Payload }) {
  return (
    <>
      {p.recompute_agrees === false && p.contradictions && p.contradictions.length > 0 && (
        <div className="flag-line">
          <Split size={13} style={{ verticalAlign: "-2px", marginRight: 6 }} />
          live-flag contradicts lockfile entries: {p.contradictions.join("; ")}
        </div>
      )}
      {p.recompute_agrees === true && (
        <div className="flag-ok">
          <Eye size={13} style={{ verticalAlign: "-2px", marginRight: 6 }} />
          live-flag recheck confirms every resolution below is still live
        </div>
      )}
      {(p.lockfiles ?? []).map((l, i) => (
        <div className="lockfile" key={i}>
          <span>
            {l.app} <span style={{ color: "var(--muted)" }}>→ {l.service}</span>
          </span>
          <span className="ver">
            {l.name}@{l.version}
          </span>
          <span style={{ color: "var(--muted)" }}>{l.resolved_at}</span>
          <span className="warn-pill">LIVE</span>
        </div>
      ))}
    </>
  );
}

function Contagion({ p }: { p: Payload }) {
  return (
    <>
      {(p.packages ?? []).map((name) => (
        <div className="lockfile" key={name}>
          <span className="ver">{name}</span>
          <span style={{ color: "var(--muted)" }}>same developer as {p.developer ?? "?"}</span>
          <span className="warn-pill">SHARES</span>
        </div>
      ))}
    </>
  );
}

function Typosquat({ p }: { p: Payload }) {
  return (
    <div>
      {(p.candidates ?? []).map((c) => (
        <div className="list-row" key={c.id}>
          <ShieldAlert size={14} style={{ color: (c.score ?? 0) >= 3 ? "var(--danger)" : "var(--muted)" }} />
          <span>
            <b>{c.name}</b>{" "}
            <span style={{ color: "var(--muted)" }}>
              ~ {c.nearest_seed ?? "?"} · {c.in_degree ?? 0} dependants
            </span>
          </span>
          <span className="scorebar">
            <span className="fill" style={{ width: `${Math.min(100, ((c.score ?? 0) / 5) * 100)}%` }} />
          </span>
          <span className="score-num">{c.score}</span>
        </div>
      ))}
    </div>
  );
}

function Blast({ p }: { p: Payload }) {
  const hops = p.levels?.map((lvl, i) => `${i + 1}: ${lvl.map((n) => n.name).join(", ")}`) ?? [];
  return (
    <div>
      <div className="flag-line">
        <TrendingUp size={13} style={{ verticalAlign: "-2px", marginRight: 6 }} />
        {p.dependant_count ?? 0} transitive dependants reach this package within 6 hops
      </div>
      {hops.length > 0 && (
        <div className="list-row">
          <span style={{ color: "var(--muted)" }}>hops</span>
          <span>{hops.join("  ·  ")}</span>
        </div>
      )}
    </div>
  );
}

function Lookup({ p }: { p: Payload }) {
  const props = p.node ?? {};
  return (
    <dl className="kv">
      {Object.entries(props)
        .filter(([, v]) => v !== null && v !== undefined && v !== "")
        .map(([k, v]) => (
          <div key={k} style={{ display: "contents" }}>
            <dt>{k}</dt>
            <dd>{typeof v === "object" ? JSON.stringify(v) : String(v)}</dd>
          </div>
        ))}
    </dl>
  );
}

export function VerdictCard({ answer }: { answer: AskResponse }) {
  const tag = INTENT_TAG[answer.intent] ?? "answer";
  const p = answer.payload ?? {};
  return (
    <div className="card">
      <div className="card-hd">
        <span className={`tag ${tag}`}>{answer.intent.toLowerCase()}?</span>
        <span className="meta">
          <b>{answer.query_count}</b> queries · {answer.latency_ms.toFixed(0)}ms
        </span>
      </div>
      <div className="card-body">
        {answer.abstain ? (
          <>
            <div className="flag-abstain">
              <TerminalSquare size={13} /> not found · reported
            </div>
            <p className="answer-text">{answer.reason}</p>
          </>
        ) : (
          <>
            <p className="answer-text">{answer.answer}</p>
            {answer.healed && <div className="reason">answered after self-heal materialized the missing data</div>}
          </>
        )}

        {!answer.abstain && renderPayload(answer.intent, p)}

        {answer.reason && !answer.abstain && <p className="reason">{answer.reason}</p>}
      </div>
      {answer.evidence_chain.length > 0 && <EvidenceChain chain={answer.evidence_chain} />}
    </div>
  );
}

function renderPayload(intent: string, p: Payload) {
  switch (intent) {
    case "EXPOSED_SERVICES":
      return <Exposed p={p} />;
    case "RESOLVED_WHILE_LIVE":
      return <Resolved p={p} />;
    case "MAINTAINER_CONTAGION":
      return p.packages && p.packages.length > 0 ? <Contagion p={p} /> : null;
    case "TYPOSQUAT_CANDIDATES":
      return p.candidates && p.candidates.length > 0 ? <Typosquat p={p} /> : null;
    case "BLAST_RADIUS":
      return p.found ? <Blast p={p} /> : null;
    case "PACKAGE_LOOKUP":
      return p.node ? <Lookup p={p} /> : null;
    default:
      return null;
  }
}
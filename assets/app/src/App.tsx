import { useEffect, useMemo, useState } from "react";
import type { Customer, Example, ExposureReport, Overview, SubgraphResponse } from "./api";
import { api } from "./api";
import { VerdictCard } from "./Verdict";
import { GraphPanel } from "./Graph";
import { ReportCard } from "./Report";
import {
  Beaker,
  Boxes,
  Command,
  Database,
  Plus,
  Radar,
  Send,
  Share2,
  ShieldAlert,
  Sparkles,
  type LucideIcon,
} from "lucide-react";

const ICONS: Record<string, LucideIcon> = {
  exposed: Beaker,
  resolved: Database,
  contagion: Share2,
  typosquat: ShieldAlert,
  blast: Boxes,
  lookup: Command,
};

function HistoryList({ turns, active, onPick }: { turns: Customer[]; active: number; onPick: (id: number) => void }) {
  return (
    <>
      <div className="history-label">session</div>
      {turns.length === 0 ? (
        <div className="history-empty">No runs yet — the terminal is quiet.</div>
      ) : (
        turns.map((c) => {
          const last = c.turns[c.turns.length - 1];
          const Icon = ICONS[last?.answer.intent ?? ""] ?? Command;
          return (
            <button
              key={c.id}
              className="history-item"
              onClick={() => onPick(c.id)}
              style={c.id === active ? { background: "rgba(0,0,0,0.06)" } : undefined}
            >
              {c.question}
              <span className="h-intent">
                <Icon size={12} style={{ verticalAlign: "-2px", marginRight: 4, color: "var(--muted)" }} />
                {last ? last.answer.intent.toLowerCase() : "…"}
              </span>
            </button>
          );
        })
      )}
    </>
  );
}

function Welcome({ examples, onAsk }: { examples: Example[]; onAsk: (q: string) => void }) {
  return (
    <div className="welcome">
      <h1>Slash</h1>
      <p>
        Queries your dependency graph on HydraDB and answers, with evidence:
        exposed services, resolved-while-live, maintainer contagion, typosquats,
        blast radius. No LLM keys — every answer is computed, and it abstains
        when the graph isn&#39;t sure.
      </p>
      <div className="chips">
        {examples.map((e) => {
          const Tag = ICONS[e.tag] ?? Command;
          return (
            <button key={e.question} className="chip" title={e.hint} onClick={() => onAsk(e.question)}>
              <Tag size={13} />
              {e.question.length > 64 ? e.question.slice(0, 62) + "…" : e.question}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function Stats({ ov }: { ov: Overview }) {
  const items = [
    { k: "nodes", v: ov.total_nodes.toLocaleString() },
    { k: "malicious", v: String(ov.malicious_versions), color: "var(--danger)" },
    { k: "typosquats", v: String(ov.typosquat_versions), color: "var(--danger)" },
    { k: "advisories", v: String(ov.advisories), color: "var(--warning)" },
  ];
  return (
    <div className="stats">
      {items.map((i) => (
        <div className="stat" key={i.k}>
          <div className="k">{i.k}</div>
          <div className="v" style={{ color: i.color ?? undefined }}>{i.v}</div>
        </div>
      ))}
      <div className="stat">
        <div className="k">node mix</div>
        <div className="v" style={{ fontSize: 13 }}>
          {Object.entries(ov.nodes)
            .map(([k, v]) => `${k} ${v}`)
            .join(" · ")}
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [active, setActive] = useState(0);
  const [input, setInput] = useState("");
  const [pending, setPending] = useState(false);
  const [ov, setOv] = useState<Overview | null>(null);
  const [health, setHealth] = useState<{ ok: boolean; label: string } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<ExposureReport | null>(null);
  const [reportBusy, setReportBusy] = useState(false);

  useEffect(() => {
    api.overview().then(setOv).catch((e) => setError(String(e)));
    api
      .health()
      .then((h) => setHealth({ ok: h.ok, label: h.hydradb }))
      .catch((e) => setHealth({ ok: false, label: String(e) }));
  }, []);

  const runReport = async () => {
    setReportBusy(true);
    setError(null);
    try {
      setReport(await api.report());
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setReportBusy(false);
    }
  };

  const ask = async (question: string) => {
    if (!question.trim() || pending) return;
    setPending(true);
    setError(null);
    setInput("");
    try {
      const answer = await api.ask(question);
      const graph = await bestGraph(answer);
      const customerId = active === 0 && customers.length === 0 ? 1 : active;
      if (active === 0 && customers.length === 0) {
        setCustomers([{ id: 1, question, turns: [{ answer, graph, t: Date.now() }] }]);
        setActive(1);
      } else {
        setCustomers((cs) =>
          cs.map((c) =>
            c.id === customerId
              ? { ...c, turns: [...c.turns, { answer, graph, t: Date.now() }] }
              : c,
          ),
        );
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setPending(false);
    }
  };

  async function bestGraph(answer: Awaited<ReturnType<typeof api.ask>>): Promise<SubgraphResponse | undefined> {
    const p = answer.payload;
    const hasNode = p?.node_id != null && (p?.found || p?.node);
    if (!hasNode) return undefined;
    const name = p?.name ?? (p?.node as { name?: string } | undefined)?.name;
    const version = p?.version ?? (p?.node as { version?: string } | undefined)?.version;
    if (!name) return undefined;
    try {
      return await api.subgraph(name, version ?? "");
    } catch {
      return undefined;
    }
  }

  const current = customers.find((c) => c.id === active);

  return (
    <div className="splash">
      <aside className="sidebar">
        <div className="sidebar-hd">
          <div className="brand">
            <Command size={17} />
            slash
            <small>hydradb</small>
          </div>
          {ov && (
            <div className="dataset">
              corpus <b>{ov.dataset}</b>
              <br />
              {ov.advisories} advisories · {ov.exposures.length > 0
                ? `${ov.exposures.length} malicious versions live in ${ov.exposures.reduce((n, e) => n + e.resolved_live.length, 0)} lockfiles`
                : "no live exposures"}
            </div>
          )}
        </div>
        <div className="sidebar-nav">
          <button className="btn-new" onClick={() => { setCustomers((cs) => [...cs, { id: nextId(cs), question: "new session", turns: [] }]); setActive(nextId(customers)); }}>
            <Plus size={14} /> new session
          </button>
        </div>
        <div className="history">
          <HistoryList turns={customers} active={active} onPick={setActive} />
        </div>
      </aside>
      <section className="main">
        <div className="topbar">
          <ShieldAlert size={15} style={{ color: "var(--accent)" }} />
          <div className="breadcrumb">
            <b>supply chain console</b> / blast radius
          </div>
          <div className="status">
            <button className="btn-scan" onClick={() => void runReport()} disabled={reportBusy}>
              <Radar size={13} />
              {reportBusy ? "scanning…" : "exposure scan"}
            </button>
            <span className={`dot ${health?.ok ? "ok" : "bad"}`} />
            {health ? health.label : "connecting…"}
          </div>
        </div>

        {ov && <Stats ov={ov} />}

        <div className="thread">
          {error && <div className="err-line">{error}</div>}

          {report && <ReportCard report={report} onClose={() => setReport(null)} />}

          {current && current.turns.length > 0 ? (
            <>
              {current.turns.map((t) => (
                <div key={t.t}>
                  <div className="msg msg-user">
                    <div className="bubble">{t.answer.question}</div>
                  </div>
                  <div className="msg">
                    <VerdictCard answer={t.answer} />
                    {t.graph && <GraphPanel graph={t.graph} />}
                  </div>
                </div>
              ))}
            </>
          ) : (
            ov && <Welcome examples={ov.examples} onAsk={ask} />
          )}

          {pending && (
            <div className="thinking">
              <span className="typing-dots"><i /><i /><i /></span>
              consulting hydradb…
            </div>
          )}

          {!current && !pending && (
            <div className="banner">
              <b>No session yet.</b> Start one in the sidebar or hit a curated question
              above to watch the pipeline decompose it into Cypher plans —
              every answer ships with its evidence chain and the graph it came from.
            </div>
          )}
        </div>

        <form
          className="askbar"
          onSubmit={(ev) => {
            ev.preventDefault();
            void ask(input);
          }}
        >
          <div className="ask-inner">
            <div className={`ask-box ${pending ? "dim" : ""}`}>
              <Sparkles size={15} style={{ color: "var(--muted)" }} />
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={pending ? "running…" : "ask the graph, e.g. is olso a typosquat of oslo?"}
                disabled={pending}
                autoFocus
              />
            </div>
            <button className="btn-go" disabled={pending || !input.trim()} aria-label="Ask">
              <Send size={16} />
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}

function nextId(cs: Customer[]): number {
  return cs.reduce((m, c) => Math.max(m, c.id), 0) + 1;
}
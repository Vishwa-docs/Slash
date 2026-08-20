import { useCallback, useEffect, useState } from "react";
import type { AskResponse, Example, ExposureReport, ProjectOverview, ProjectSummary, Session, SessionTurn, SubgraphResponse } from "./api";
import { api } from "./api";
import { VerdictCard } from "./Verdict";
import { GraphPanel } from "./Graph";
import { ReportCard } from "./Report";
import {
  Beaker,
  Boxes,
  Command,
  Database,
  FolderGit2,
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

const WELCOME =
  "Paste Github Repos, generate their dependency graph and every CVE that touches them — queried live on HydraDB with an evidence chain. When the graph can't answer, Slash tries to heal itself first, then logs the gap to the support report.";

function Welcome({ examples, onAsk }: { examples: Example[]; onAsk: (q: string) => void }) {
  return (
    <div className="welcome">
      <h1>Slash</h1>
      <p>{WELCOME}</p>
      <div className="chips">
        {examples.map((e) => {
          const Tag = ICONS[e.tag ?? ""] ?? Command;
          return (
            <button
              key={e.question}
              className="chip"
              title={e.hint}
              onClick={() => onAsk(e.question)}
            >
              <Tag size={13} />
              {e.question.length > 80 ? e.question.slice(0, 78) + "…" : e.question}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function Stats({ stats }: { stats: ProjectOverview["stats"] }) {
  const items = [
    { k: "versions", v: (stats.versions ?? 0).toLocaleString() },
    { k: "services", v: String(stats.services ?? 0) },
    { k: "advisories", v: String(stats.advisories ?? 0), color: "var(--warning)" },
    { k: "malicious", v: String(stats.malicious ?? 0), color: "var(--danger)" },
    { k: "nodes", v: (stats.nodes ?? 0).toLocaleString() },
  ];
  return (
    <div className="stats">
      {items.map((i) => (
        <div className="stat" key={i.k}>
          <div className="k">{i.k}</div>
          <div className="v" style={{ color: i.color ?? undefined }}>{i.v}</div>
        </div>
      ))}
    </div>
  );
}

function ProjectList({
  projects,
  active,
  onPick,
  onAdd,
}: {
  projects: ProjectSummary[];
  active: string | null;
  onPick: (id: string) => void;
  onAdd: () => void;
}) {
  return (
    <>
      <div className="sidebar-sub">
        projects <button className="btn-mini" onClick={onAdd} title="Click here to add a new repo — paste GitHub URLs and Slash generates each dependency graph" aria-label="add project"><Plus size={12} /> add</button>
      </div>
      {projects.length === 0 ? (
        <div className="history-empty">No projects yet. Tip: click «add» above, then paste a GitHub repo URL to generate its graph.</div>
      ) : (
        projects.map((p) => (
          <button
            key={p.id}
            className="history-item project-item"
            onClick={() => onPick(p.id)}
            style={p.id === active ? { background: "rgba(0,0,0,0.06)" } : undefined}
          >
            <FolderGit2 size={14} style={{ marginRight: 6, color: "var(--muted)", flexShrink: 0 }} />
            <span className="project-name">
              {p.repo}
              {p.demo && <span className="demo-pill">demo</span>}
            </span>
            <span className="h-intent">{p.advisory_count} adv</span>
          </button>
        ))
      )}
    </>
  );
}

function normalizeTurn(raw: unknown, fallbackT: number): SessionTurn {
  if (
    typeof raw === "object" &&
    raw !== null &&
    "answer" in raw &&
    typeof (raw as { answer: unknown }).answer === "object"
  ) {
    const wrapped = raw as { answer: AskResponse; t?: number };
    return { answer: wrapped.answer, t: wrapped.t ?? fallbackT };
  }
  // legacy flat meta (pre-2026-08-20) — answer text and the rest of the meta lived
  // at the top level of the turn object.
  return { answer: raw as AskResponse, t: fallbackT };
}

function defaultProject(projects: ProjectSummary[]): ProjectSummary {
  // Prefer the most recent non-demo project; fall back to the demo seed so a
  // fresh clone (demo-only) still lands on the demo repo.
  const nonDemo = projects.filter((p) => !p.demo);
  if (nonDemo.length > 0) {
    return nonDemo.slice().sort((a, b) => (b.generated_at ?? 0) - (a.generated_at ?? 0))[0];
  }
  return projects[0];
}

function SessionList({
  sessions,
  active,
  onPick,
  onNew,
}: {
  sessions: Session[];
  active: string | null;
  onPick: (id: string) => void;
  onNew: () => void;
}) {
  return (
    <>
      <div className="sidebar-sub">
        sessions <button className="btn-mini" onClick={onNew} aria-label="new session"><Plus size={12} /> new</button>
      </div>
      {sessions.length === 0 ? (
        <div className="history-empty">No sessions yet. Ask something to start a thread.</div>
      ) : (
        sessions.map((s) => (
          <button
            key={s.id}
            className="history-item"
            onClick={() => onPick(s.id)}
            style={s.id === active ? { background: "rgba(0,0,0,0.06)" } : undefined}
          >
            <span className="s-title">{s.title}</span>
          </button>
        ))
      )}
    </>
  );
}

export default function App() {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [proj, setProj] = useState<ProjectOverview | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [turnsBySession, setTurnsBySession] = useState<Record<string, SessionTurn[]>>({});

  const [input, setInput] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [bootError, setBootError] = useState<string | null>(null);
  const [health, setHealth] = useState<{ ok: boolean; label: string } | null>(null);

  const [showAdd, setShowAdd] = useState(false);
  const [addUrl, setAddUrl] = useState("");
  const [adding, setAdding] = useState(false);
  const [report, setReport] = useState<ExposureReport | null>(null);
  const [reportBusy, setReportBusy] = useState(false);
  const [tipsOpen, setTipsOpen] = useState<boolean>(() => localStorage.getItem("slash.tips_dismissed") !== "1");

  const reloadProjects = useCallback(async () => {
    try {
      const res = await api.projects();
      setProjects(res.projects);
      if (res.projects.length > 0) {
        setActiveId((prev) =>
          res.projects.some((p) => p.id === prev)
            ? prev
            : defaultProject(res.projects).id,
        );
      }
    } catch (e) {
      setBootError(String(e));
    }
  }, []);

  const reloadHealth = useCallback(() => {
    api.health().then((h) => setHealth({ ok: h.ok, label: h.hydradb })).catch(() => setHealth({ ok: false, label: "hydradb offline" }));
  }, []);

  useEffect(() => {
    setBootError(null);
    setError(null);
    void reloadProjects();
    reloadHealth();
  }, [reloadProjects, reloadHealth]);

  const loadProject = useCallback(async (id: string) => {
    setActiveId(id);
    try {
      const o = await api.projectOverview(id);
      setProj(o);
      setSessions(o.sessions);
      setTurnsBySession(
        Object.fromEntries(
          o.sessions.map((s) => [s.id, s.turns.map((t) => normalizeTurn(t, s.created_at * 1000))]),
        ),
      );
      if (o.sessions.length > 0) setActiveSessionId(o.sessions[0].id);
      else setActiveSessionId(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, []);

  const addProject = async () => {
    const urls = addUrl
      .split(/[\n,;]+/)
      .map((u) => u.trim().replace(/\/+$/, ""))
      .filter(Boolean);
    if (urls.length === 0 || adding) return;
    setAdding(true);
    setError(null);
    try {
      const results = await Promise.all(urls.map((u) => api.addProject(u)));
      setAddUrl("");
      setShowAdd(false);
      await reloadProjects();
      if (results.length > 0) await loadProject(results[0].id);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setAdding(false);
    }
  };

  const newSession = async () => {
    if (!activeId) return;
    try {
      const s = await api.newSession(activeId);
      await loadProject(activeId);
      setActiveSessionId(s.id);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const runScan = async () => {
    if (!activeId || reportBusy) return;
    setReportBusy(true);
    setError(null);
    try {
      setReport(await api.projectScan(activeId));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setReportBusy(false);
    }
  };

  const ask = async (question: string) => {
    if (!question.trim() || pending || !activeId) return;
    setPending(true);
    setError(null);
    setInput("");
    try {
      let sid = activeSessionId;
      if (!sid) {
        const s = await api.newSession(activeId);
        sid = s.id;
        setActiveSessionId(s.id);
      }
      const answer = await api.projectAsk(activeId, question, sid);
      const graph = await bestGraph(answer);
      const turn: SessionTurn = { answer, graph, t: Date.now() };
      setTurnsBySession((map) => ({ ...map, [sid!]: [...(map[sid!] ?? []), turn] }));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setPending(false);
    }
  };

  async function bestGraph(answer: AskResponse): Promise<SubgraphResponse | undefined> {
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

  const activeTurns = activeSessionId ? turnsBySession[activeSessionId] ?? [] : [];

  return (
    <div className="splash">
      <aside className="sidebar">
        <div className="sidebar-hd">
          <div className="brand">
            <Command size={17} />
            slash
            <small>hydradb</small>
          </div>
        </div>

        <div className="sidebar-nav">
          <ProjectList
            projects={projects}
            active={activeId}
            onPick={(id) => void loadProject(id)}
            onAdd={() => setShowAdd((s) => !s)}
          />
          {showAdd && (
            <form
              className="add-form"
              onSubmit={(e) => {
                e.preventDefault();
                void addProject();
              }}
            >
              <textarea
                value={addUrl}
                onChange={(e) => setAddUrl(e.target.value)}
                placeholder={
                  "https://github.com/owner/repo\n(add more — one URL per line — they all get generated)"
                }
                disabled={adding}
                autoFocus
                rows={3}
              />
              <button className="btn-mini add-go" disabled={adding || !addUrl.trim()}>
                {adding ? "generating…" : "generate graph"}
              </button>
            </form>
          )}
        </div>

        {proj && (
          <div className="history">
            <SessionList
              sessions={sessions}
              active={activeSessionId}
              onPick={setActiveSessionId}
              onNew={() => void newSession()}
            />
          </div>
        )}
      </aside>

      <section className="main">
        <div className="topbar">
          <ShieldAlert size={15} style={{ color: "var(--accent)" }} />
          <div className="breadcrumb">
            <b>hydradb</b>
            {proj ? ` / ${proj.project.repo}` : " / select a project"}
          </div>
          <div className="status">
            <button
              className="btn-scan"
              onClick={() => void runScan()}
              disabled={reportBusy || !activeId}
              title="Click here to run the exposure scan — an advisory report over this repo's graph"
            >
              <Radar size={13} />
              {reportBusy ? "scanning…" : "exposure scan"}
            </button>
            <span className={`dot ${health?.ok ? "ok" : "bad"}`} />
            {health ? health.label : "connecting…"}
          </div>
        </div>

        {tipsOpen ? (
          <div className="qtips" role="note">
            <span className="tip">
              <span className="tip-k">1</span> click <b>«add»</b> in the sidebar to paste a new GitHub repo — Slash generates its
              dependency graph and every CVE that touches it
            </span>
            <span className="tip">
              <span className="tip-k">2</span> click <b>«exposure scan»</b> (top-right) for a repo's advisory exposure report
            </span>
            <span className="tip">
              <span className="tip-k">3</span> ask the graph below, or hit a question chip — every answer ships its evidence chain
            </span>
            <button
              className="tip-x"
              title="Dismiss these tips"
              onClick={() => {
                localStorage.setItem("slash.tips_dismissed", "1");
                setTipsOpen(false);
              }}
            >
              ×
            </button>
          </div>
        ) : (
          <button
            className="tip-reopen"
            title="Show the onboarding tips again"
            onClick={() => setTipsOpen(true)}
          >
            ?
          </button>
        )}

        {proj && <Stats stats={proj.stats} />}

        <div className="thread">
          {bootError && (
            <div className="err-line">
              couldn't reach the local API ({bootError}). Is <code>scripts/serve.py</code> running next to a live HydraDB?
              <button className="err-retry" onClick={() => { void reloadProjects(); reloadHealth(); }}>retry</button>
            </div>
          )}
          {error && <div className="err-line">{error}</div>}

          {report && <ReportCard report={report} onClose={() => setReport(null)} />}

          {activeTurns.length > 0 ? (
            activeTurns.map((t, i) => (
              <div key={`${t.answer.question}-${i}`}>
                <div className="msg msg-user">
                  <div className="bubble">{t.answer.question}</div>
                </div>
                <div className="msg">
                  <VerdictCard answer={t.answer} />
                  {t.graph && <GraphPanel graph={t.graph} />}
                </div>
              </div>
            ))
          ) : (
            proj ? (
              <Welcome examples={proj.examples} onAsk={ask} />
            ) : (
              <div className="banner">
                <b>Select a project.</b> Pick one in the sidebar or add a GitHub repo to
                generate its dependency graph and every CVE that touches it.
              </div>
            )
          )}

          {pending && (
            <div className="thinking">
              <span className="typing-dots"><i /><i /><i /></span>
              consulting hydradb…
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
                placeholder={
                  pending
                    ? "running…"
                    : proj
                      ? `ask the graph about ${proj.project.repo}…`
                      : "pick a project to start…"
                }
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
import type { ExposureReport } from "./api";
import { Activity, ShieldAlert, ShieldCheck, X } from "lucide-react";

function fmtTs(ts: number): string {
  return new Date(ts * 1000).toISOString().slice(0, 10);
}

export function ReportCard({ report, onClose }: { report: ExposureReport; onClose: () => void }) {
  const t = report.totals;
  return (
    <div className="card" style={{ marginBottom: 14 }}>
      <div className="card-hd">
        <span className="tag exposed">
          <Activity size={11} style={{ verticalAlign: "-1px", marginRight: 5 }} />
          exposure report
        </span>
        <span className="meta">
          {report.advisories_checked} advisories · {report.generated_ms}ms ·{" "}
          {(() => {
            const worst = report.exposures.filter((e) => !e.recompute_agrees).length;
            return worst > 0 ? (
              <span style={{ color: "var(--danger)" }}>
                <ShieldAlert size={12} style={{ verticalAlign: "-2px", marginRight: 3 }} />
                {worst} contradiction{worst === 1 ? "" : "s"}
              </span>
            ) : (
              <span style={{ color: "var(--success)" }}>
                <ShieldCheck size={12} style={{ verticalAlign: "-2px", marginRight: 3 }} />
                recompute agrees
              </span>
            );
          })()}
        </span>
        <button
          onClick={onClose}
          aria-label="dismiss report"
          style={{
            marginLeft: "auto",
            background: "none",
            border: "none",
            color: "var(--muted)",
            display: "inline-flex",
            padding: 2,
          }}
        >
          <X size={14} />
        </button>
      </div>
      <div className="card-body">
        <div className="stats" style={{ padding: 0, gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))" }}>
          <div className="stat">
            <div className="k">services exposed</div>
            <div className="v" style={{ color: "var(--danger)" }}>{t.services_exposed}</div>
          </div>
          <div className="stat">
            <div className="k">apps at risk</div>
            <div className="v" style={{ color: "var(--warning)" }}>{t.apps_at_risk}</div>
          </div>
          <div className="stat">
            <div className="k">live resolutions</div>
            <div className="v">{t.live_resolutions}</div>
          </div>
          <div className="stat">
            <div className="k">advisories present</div>
            <div className="v">{report.advisories_present}</div>
          </div>
        </div>

        {report.exposures.map((e) => (
          <div key={e.advisory_id} className="lockfile" style={{ marginTop: 12 }}>
            <span>
              <b>{e.advisory_id}</b> · <span className="ver">{e.name}@{e.version}</span>
            </span>
            <span>
              <span className="services-row" style={{ marginTop: 0, gap: 4 }}>
                {(e.services.length ? e.services : ["—"]).map((s) => (
                  <span className="service" key={s} style={{ fontSize: 11, padding: "2px 7px" }}>
                    {s}
                  </span>
                ))}
              </span>
            </span>
            <span style={{ color: "var(--muted)" }}>
              {e.appearing.join(" · ") || "no app reaches it"} · {e.lockfile_count} live
            </span>
            <span className={e.recompute_agrees ? "flag-ok" : "flag-line"} style={{ margin: 0, whiteSpace: "nowrap" }}>
              {e.recompute_agrees ? "agrees" : "CONTRADICTS live flag"}
            </span>
            {e.resolved_while_live.map((lf) => (
              <div key={`${e.advisory_id}-${lf.app}`} className="pin-meta" style={{ fontSize: 11.5, color: "var(--muted)" }}>
                {lf.app} → {lf.service} resolved <b>{lf.name}@{lf.version}</b> at {fmtTs(lf.resolved_at)}
              </div>
            ))}
          </div>
        ))}

        <p className="reason" style={{ marginTop: 12 }}>
          generated from the graph · every resolution above re-checked against the
          publish/validity window semantics
        </p>
      </div>
    </div>
  );
}
import { useMemo } from "react";
import type { SubgraphResponse } from "./api";
import { Share2 } from "lucide-react";

interface Placed {
  id: number;
  x: number;
  y: number;
  name: string;
  version: string;
  root: boolean;
}

const W = 720;
const H = 320;
const RAD = 105;

export function GraphPanel({ graph }: { graph: SubgraphResponse }) {
  const { placed, edges } = useMemo(() => {
    const byId = new Map(graph.nodes.map((n) => [n.id, n]));
    const root = byId.get(graph.node_id);

    const placed: Placed[] = [];
    if (root) {
      placed.push({ id: root.id, x: 0, y: 0, name: root.name ?? "?", version: root.version ?? "", root: true });
    }
    const others = graph.nodes.filter((n) => n.id !== graph.node_id);
    const ring: Placed[] = others.map((n, i) => {
      const a = (i / Math.max(others.length, 1)) * Math.PI * 2 - Math.PI / 2;
      return {
        id: n.id,
        x: Math.cos(a) * RAD,
        y: Math.sin(a) * RAD,
        name: n.name ?? "?",
        version: n.version ?? "",
        root: false,
      };
    });
    placed.push(...ring);
    const pos = new Map(placed.map((n) => [n.id, n]));

    const edges = graph.edges
      .map((e) => {
        const a = pos.get(e.src);
        const b = pos.get(e.dst);
        if (!a || !b) return null;
        return { sx: a.x, sy: a.y, dx: b.x, dy: b.y, type: e.type };
      })
      .filter((e): e is NonNullable<typeof e> => e !== null);
    return { placed, edges };
  }, [graph]);

  return (
    <div className="graph-panel">
      <div className="gp-hd">
        <Share2 size={12} />
        dependency view @ {graph.node_id} · {graph.nodes.length} nodes · {graph.edges.length} edges ·{" "}
        {graph.elapsed_ms.toFixed(1)}ms
      </div>
      <svg viewBox={`${-W / 2} ${-H / 2} ${W} ${H}`} role="img" aria-label="nearby dependency graph">
        <defs>
          <marker id="arw" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#b9b2ac" />
          </marker>
        </defs>
        {edges.map((e, i) => (
          <line
            key={i}
            x1={e.sx}
            y1={e.sy}
            x2={e.dx}
            y2={e.dy}
            stroke="#b9b2ac"
            strokeWidth="1"
            markerEnd="url(#arw)"
          />
        ))}
        {placed.map((n) =>
          n.root ? (
            <g key={n.id} transform={`translate(${n.x} ${n.y})`}>
              <rect x="-58" y="-12" width="116" height="24" rx="2" fill="var(--accent)" />
              <text x="0" y="4" textAnchor="middle" fontSize="11" fill="#fff" fontFamily="inherit">
                {n.name}@{n.version}
              </text>
            </g>
          ) : (
            <g key={n.id} transform={`translate(${n.x} ${n.y})`}>
              <rect x="-46" y="-11" width="92" height="22" rx="2" fill="var(--bg)" stroke="var(--ink)" strokeWidth="1" />
              <text x="0" y="4" textAnchor="middle" fontSize="10.5" fill="var(--ink)" fontFamily="inherit">
                {n.name}
              </text>
            </g>
          ),
        )}
      </svg>
    </div>
  );
}
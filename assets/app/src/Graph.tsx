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
  malicious: boolean;
}

const W = 760;
const H = 360;

function forceLayout(nodes: SubgraphResponse["nodes"], edges: SubgraphResponse["edges"]) {
  const byId = new Map(nodes.map((n) => [n.id, n]));
  const root = byId.get(nodes[0]?.id ?? 0);

  const placed: Placed[] = [];
  const idx = new Map<number, number>();
  nodes.forEach((n, i) => {
    idx.set(n.id, i);
    const a = (i / Math.max(nodes.length, 1)) * Math.PI * 2;
    placed.push({
      id: n.id,
      x: Math.cos(a) * 90 + (i % 3) * 6,
      y: Math.sin(a) * 90 + (i % 2) * 6,
      name: n.name ?? "?",
      version: n.version ?? "",
      root: n.id === (root?.id ?? -1),
      malicious: false,
    });
  });

  const adj = new Map<number, number[]>();
  for (const e of edges) {
    adj.set(e.src, [...(adj.get(e.src) ?? []), e.dst]);
    adj.set(e.dst, [...(adj.get(e.dst) ?? []), e.src]);
  }
  if (root) {
    // mark malicious nodes (any node id that appears in the graph with no version is package-level; keep simple)
  }

  const vel = new Map<number, { vx: number; vy: number }>(nodes.map((n) => [n.id, { vx: 0, vy: 0 }]));

  const dt = 0.35;
  for (let iter = 0; iter < 90; iter++) {
    for (const a of nodes) {
      const pa = placed[idx.get(a.id)!];
      for (const b of nodes) {
        if (a.id === b.id) continue;
        const pb = placed[idx.get(b.id)!];
        const dx = pa.x - pb.x;
        const dy = pa.y - pb.y;
        const d2 = Math.max(dx * dx + dy * dy, 1);
        const f = (2600 / d2) * dt;
        const v = vel.get(a.id)!;
        v.vx += (dx / Math.sqrt(d2)) * f;
        v.vy += (dy / Math.sqrt(d2)) * f;
      }
      const v = vel.get(a.id)!;
      v.vx += (-pa.x) * 0.01 * dt;
      v.vy += (-pa.y) * 0.01 * dt;
    }
    for (const e of edges) {
      const pa = placed[idx.get(e.src)!];
      const pb = placed[idx.get(e.dst)!];
      if (!pa || !pb) continue;
      const dx = pb.x - pa.x;
      const dy = pb.y - pa.y;
      const d = Math.max(Math.sqrt(dx * dx + dy * dy), 1);
      const want = 70;
      const f = ((d - want) * 0.012) * dt;
      const ux = dx / d;
      const uy = dy / d;
      const va = vel.get(e.src)!;
      const vb = vel.get(e.dst)!;
      va.vx += ux * f;
      va.vy += uy * f;
      vb.vx -= ux * f;
      vb.vy -= uy * f;
    }
    for (const n of nodes) {
      const v = vel.get(n.id)!;
      const p = placed[idx.get(n.id)!];
      p.x += v.vx;
      p.y += v.vy;
      v.vx *= 0.82;
      v.vy *= 0.82;
    }
  }

  // scale to fit
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
  for (const p of placed) {
    minX = Math.min(minX, p.x); maxX = Math.max(maxX, p.x);
    minY = Math.min(minY, p.y); maxY = Math.max(maxY, p.y);
  }
  const cx = (minX + maxX) / 2, cy = (minY + maxY) / 2;
  const scale = Math.min((W - 80) / Math.max(maxX - minX, 1), (H - 80) / Math.max(maxY - minY, 1), 2.2);
  for (const p of placed) {
    p.x = (p.x - cx) * scale;
    p.y = (p.y - cy) * scale;
  }
  return { placed, root };
}

export function GraphPanel({ graph }: { graph: SubgraphResponse }) {
  const { placed, root } = useMemo(() => forceLayout(graph.nodes, graph.edges), [graph]);
  const pos = new Map(placed.map((n) => [n.id, n]));

  const edges = graph.edges
    .map((e) => {
      const a = pos.get(e.src);
      const b = pos.get(e.dst);
      if (!a || !b) return null;
      return { sx: a.x, sy: a.y, dx: b.x, dy: b.y };
    })
    .filter((e): e is NonNullable<typeof e> => e !== null);

  const deg = new Map<number, number>();
  for (const e of graph.edges) {
    deg.set(e.src, (deg.get(e.src) ?? 0) + 1);
    deg.set(e.dst, (deg.get(e.dst) ?? 0) + 1);
  }

  return (
    <div className="graph-panel" style={{ overflow: "hidden" }}>
      <div className="gp-hd">
        <Share2 size={12} />
        dependency view @ {graph.node_id} · {graph.nodes.length} nodes · {graph.edges.length} edges ·{" "}
        {graph.elapsed_ms.toFixed(1)}ms
      </div>
      <svg viewBox={`-${W / 2} -${H / 2} ${W} ${H}`} role="img" aria-label="force-directed dependency graph">
        <defs>
          <marker id="arw" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--hairline)" />
          </marker>
        </defs>
        {edges.map((e, i) => (
          <line
            key={i}
            x1={e.sx}
            y1={e.sy}
            x2={e.dx}
            y2={e.dy}
            stroke="var(--hairline)"
            strokeWidth="1"
            markerEnd="url(#arw)"
          />
        ))}
        {placed.map((n) => {
          const d = deg.get(n.id) ?? 0;
          const w = Math.min(140, 46 + d * 8);
          const isRoot = n.id === root?.id;
          const fill = isRoot ? "var(--accent)" : "var(--bg)";
          const stroke = isRoot ? "var(--accent)" : n.malicious ? "var(--danger)" : "var(--ink)";
          const textFill = isRoot ? "#fff" : n.malicious ? "var(--danger)" : "var(--ink)";
          return (
            <g key={n.id} transform={`translate(${n.x} ${n.y})`}>
              <rect x={-w / 2} y={-12} width={w} height="24" rx="4" fill={fill} stroke={stroke} strokeWidth="1" />
              <text x="0" y="4" textAnchor="middle" fontSize="10.5" fill={textFill} fontWeight={isRoot ? 700 : 400} fontFamily="inherit">
                {n.name}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
"""Slash query layer: parameterized Cypher builders + live execution.

Builders (`plan_*`) are pure — they return the exact query steps without
touching the client, so the app can render the "live query console" honestly.
Executors (`run_*`) run those steps against HydraDB, accumulate rows, and
capture per-step latency for the evidence chain.

Every builder/executor takes a `lens` (defaults to SUPPLY_CHAIN, byte-identical
output to the pre-lens queries). The five primitives are schema-agnostic: a
different Lens swaps node labels/relations + vocabulary so the same engine
answers dependency-graph *and* fraud/AML graphs.

Bounded to the documented OpenCypher subset. Because HydraDB rejects
`x.id IN $list` and UNWIND->node lookups, reverse closures are computed one
hop at a time with the indexed `(v {id: $id})` pattern (ADR-0007).
"""

from __future__ import annotations

import difflib
import time
from dataclasses import dataclass

from src.hydradb_client import HydraDBClient, QueryResult
from src.lens import SUPPLY_CHAIN, Lens
from src.schema import MAX_HOPS


@dataclass
class QueryStep:
    cypher: str
    params: dict
    purpose: str


@dataclass
class StepResult:
    step: QueryStep
    result: QueryResult


def _lookup_tpl(lens: Lens) -> str:
    return (
        f"MATCH (v:{lens.version_node} {{name: $name, version: $version}}) "
        f"RETURN v.id AS id, v.name AS name, v.version AS version, "
        f"v.published_at AS published_at, v.valid_until AS valid_until, "
        f"v.{lens.malicious_field} AS malicious, v.advisory_id AS advisory_id, "
        f"v.is_typosquat AS is_typosquat"
    )


def _latest_tpl(lens: Lens) -> str:
    return (
        f"MATCH (v:{lens.version_node} {{name: $name}}) "
        "RETURN v.id AS id, v.name AS name, v.version AS version, v.published_at AS published_at, "
        f"v.valid_until AS valid_until, v.{lens.malicious_field} AS malicious, "
        f"v.advisory_id AS advisory_id, v.is_typosquat AS is_typosquat "
        "ORDER BY v.published_at DESC LIMIT 1"
    )


def _parent_tpl(lens: Lens) -> str:
    return (
        f"MATCH (u:{lens.version_node})-[:{lens.depend_rel}]->"
        f"(v:{lens.version_node} {{id: $id}}) "
        "RETURN DISTINCT u.id AS id, u.name AS name, u.version AS version"
    )


def _service_edges_tpl(lens: Lens) -> str:
    return (
        f"MATCH (s:{lens.resource_node} {{name: $svc}})-[:{lens.uses_rel}]->"
        f"(lf:{lens.consumption_node})-[r:{lens.resolves_rel}]->(v:{lens.version_node}) "
        "RETURN lf.id AS lockfile_id, lf.app AS app, lf.resolved_at AS resolved_at, "
        "v.id AS version_id, v.name AS name, v.version AS version, "
        "v.published_at AS published_at, v.valid_until AS valid_until, "
        "r.at AS at, r.was_resolved_while_live AS flag"
    )


def plan_lookup(name: str, version: str, lens: Lens = SUPPLY_CHAIN) -> QueryStep:
    return QueryStep(
        _lookup_tpl(lens), {"name": name, "version": version}, "locate package version"
    )


def plan_latest_version(name: str, lens: Lens = SUPPLY_CHAIN) -> QueryStep:
    return QueryStep(
        _latest_tpl(lens),
        {"name": name},
        f"latest published version of {name}",
    )


def plan_parents(version_id: int, lens: Lens = SUPPLY_CHAIN) -> QueryStep:
    return QueryStep(
        _parent_tpl(lens),
        {"id": version_id},
        f"incoming {lens.depend_rel} hop for v{version_id}",
    )


def plan_service_edges(service: str, lens: Lens = SUPPLY_CHAIN) -> QueryStep:
    return QueryStep(
        _service_edges_tpl(lens),
        {"svc": service},
        f"service {service} lockfile resolutions",
    )


def plan_service_names(lens: Lens = SUPPLY_CHAIN) -> QueryStep:
    return QueryStep(
        f"MATCH (s:{lens.resource_node}) RETURN s.name AS name", {}, "service catalog"
    )


def plan_popular_packages(lens: Lens = SUPPLY_CHAIN) -> QueryStep:
    return QueryStep(
        f"MATCH (n:{lens.entity_node} {{popular: true}}) RETURN n.name AS name, n.id AS id",
        {},
        "popular packages",
    )


def plan_typosquat_candidates(
    since: int | None = None, lens: Lens = SUPPLY_CHAIN
) -> QueryStep:
    return QueryStep(
        f"MATCH (v:{lens.version_node}) WHERE v.popular = false "
        "AND (v.deprecated = true OR v.published_at >= $since) "
        "RETURN v.id AS id, v.name AS name, v.published_at AS published_at, v.deprecated AS deprecated",
        {"since": since or 0},
        "typosquat-surface versions (non-popular; deprecated or recent)",
    )


def plan_in_degree(version_id: int, lens: Lens = SUPPLY_CHAIN) -> QueryStep:
    return QueryStep(
        f"MATCH (u:{lens.version_node})-[:{lens.depend_rel}]->"
        f"(v:{lens.version_node} {{id: $id}}) RETURN count(u.id) AS degree",
        {"id": version_id},
        "in-degree (dependants) of a version",
    )


def plan_subgraph_out(
    node_id: int, depth: int, lens: Lens = SUPPLY_CHAIN, rel: str | None = None
) -> QueryStep:
    rel = rel or lens.depend_rel
    return QueryStep(
        f"MATCH (a:{lens.version_node} {{id: $id}})-[:{rel}*1..{depth}]->(b) "
        "RETURN b.id AS id, b.name AS name, b.version AS version",
        {"id": node_id},
        f"outgoing {rel} subgraph depth {depth}",
    )


def plan_subgraph_in(node_id: int, lens: Lens = SUPPLY_CHAIN) -> QueryStep:
    return QueryStep(
        f"MATCH (a)-[:{lens.depend_rel}]->(b:{lens.version_node} {{id: $id}}) "
        "RETURN a.id AS id, a.name AS name, a.version AS version",
        {"id": node_id},
        "incoming DEPENDS_ON neighbours",
    )


def execute(client: HydraDBClient, steps: list[QueryStep]) -> list[StepResult]:
    return [StepResult(s, client.query(s.cypher, s.params)) for s in steps]


def total_elapsed(step_results: list[StepResult]) -> float:
    return sum(r.result.elapsed_ms for r in step_results)


# --- Executors -----------------------------------------------------------------


def _lookup(
    client: HydraDBClient, name: str, version: str, lens: Lens = SUPPLY_CHAIN
) -> tuple[QueryStep, StepResult, dict | None]:
    step = plan_lookup(name, version, lens)
    res = execute(client, [step])[0]
    return step, res, res.result.rows[0] if res.result.rows else None


def run_blast_radius(
    client: HydraDBClient,
    name: str,
    version: str,
    max_hops: int = MAX_HOPS,
    lens: Lens = SUPPLY_CHAIN,
) -> dict:
    step, res, node = _lookup(client, name, version, lens)
    if node is None:
        return {
            "found": False,
            "steps": [(step, res)],
            "elapsed_ms": res.result.elapsed_ms,
        }
    steps: list = [(step, res)]
    seen: set[int] = set()
    levels: list[list[dict]] = []
    frontier = [node["id"]]
    for depth in range(1, max_hops + 1):
        level_steps: list = []
        level_nodes: list[dict] = []
        for pid in frontier:
            s = plan_parents(pid, lens)
            r = execute(client, [s])[0]
            level_steps.append((s, r))
            for row in r.result.rows:
                uid = row["id"]
                if uid not in seen:
                    seen.add(uid)
                    level_nodes.append(
                        {
                            "id": uid,
                            "name": row["name"],
                            "version": row["version"],
                            "depth": depth,
                        }
                    )
        if not level_nodes:
            break
        levels.append(level_nodes)
        steps.extend(level_steps)
        frontier = [n["id"] for n in level_nodes]
    return {
        "found": True,
        "node": node,
        "levels": levels,
        "dependant_ids": sorted(seen),
        "dependant_count": len(seen),
        "steps": steps,
        "elapsed_ms": total_elapsed([r for _, r in steps]),
        "query_count": len(steps),
    }


def run_exposed_services(
    client: HydraDBClient,
    name: str,
    version: str,
    max_hops: int = MAX_HOPS,
    lens: Lens = SUPPLY_CHAIN,
) -> dict:
    br = run_blast_radius(client, name, version, max_hops=max_hops, lens=lens)
    if not br["found"]:
        return {
            "found": False,
            "services": [],
            "path_rows": [],
            "steps": br["steps"],
            "elapsed_ms": br["elapsed_ms"],
            "blast_radius": br,
        }
    closure: set[int] = set(br["dependant_ids"]) | {br["node"]["id"]}
    steps: list = list(br["steps"])
    svc_step = plan_service_names(lens)
    svc_res = execute(client, [svc_step])[0]
    steps.append((svc_step, svc_res))
    service_rows: list[dict] = []
    for svc_row in svc_res.result.rows:
        s = plan_service_edges(svc_row["name"], lens)
        r = execute(client, [s])[0]
        steps.append((s, r))
        service_rows.extend(
            {**row, "service": svc_row["name"]}
            for row in r.result.rows
            if row["version_id"] in closure
        )
    paths = sorted(
        (
            {
                "service": r["service"],
                "lockfile_id": r["lockfile_id"],
                "app": r["app"],
                "resolved_at": r["resolved_at"],
                "version_name": r["name"],
                "version": r["version"],
                "version_id": r["version_id"],
                "published_at": r["published_at"],
                "valid_until": r["valid_until"],
                "at": r["at"],
                "flag": r["flag"],
            }
            for r in service_rows
        ),
        key=lambda r: (r["service"], r["version_name"], r["version"]),
    )
    services = sorted({r["service"] for r in service_rows})
    return {
        "found": True,
        "services": services,
        "path_rows": paths,
        "steps": steps,
        "elapsed_ms": total_elapsed([r for _, r in steps]),
        "query_count": len(steps),
        "blast_radius": {
            k: br[k] for k in ("node", "levels", "dependant_ids", "dependant_count")
        },
    }


def run_resolved_while_live(
    client: HydraDBClient,
    name: str,
    version: str,
    max_hops: int = MAX_HOPS,
    lens: Lens = SUPPLY_CHAIN,
) -> dict:
    exp = run_exposed_services(client, name, version, max_hops=max_hops, lens=lens)
    if not exp["found"]:
        return {
            "found": False,
            "lockfiles": [],
            "recompute_agrees": True,
            "steps": exp["steps"],
            "elapsed_ms": exp["elapsed_ms"],
        }
    bad = exp["blast_radius"]["node"]
    window_locks: list[dict] = []
    mismatches: list[dict] = []
    for r in exp["path_rows"]:
        in_window = bool(bad["published_at"] <= r["resolved_at"] <= bad["valid_until"])
        row = {
            **{
                k: r[k]
                for k in (
                    "service",
                    "lockfile_id",
                    "app",
                    "version_name",
                    "version",
                    "version_id",
                )
            },
            "resolved_at": r["resolved_at"],
            "was_resolved_while_live": in_window,
        }
        if in_window:
            window_locks.append(row)
        if r["version_id"] == bad["id"]:
            recompute = bool(r["published_at"] <= r["at"] <= r["valid_until"])
            if recompute != r.get("flag"):
                mismatches.append(
                    {
                        "name": r["version_name"],
                        "version": r["version"],
                        "at": r["at"],
                        "stored_flag": r.get("flag"),
                        "recomputed_flag": recompute,
                    }
                )
    steps = exp["steps"]
    return {
        "found": True,
        "node": bad,
        "lockfiles": window_locks,
        "services": exp["services"],
        "recompute_agrees": not mismatches,
        "contradictions": mismatches,
        "steps": steps,
        "elapsed_ms": exp["elapsed_ms"],
        "query_count": exp["query_count"],
    }


def run_package_lookup(
    client: HydraDBClient,
    name: str,
    version: str | None = None,
    lens: Lens = SUPPLY_CHAIN,
) -> dict:
    steps: list = []
    step = (
        plan_lookup(name, version, lens) if version else plan_latest_version(name, lens)
    )
    res = execute(client, [step])[0]
    steps.append((step, res))
    node = res.result.rows[0] if res.result.rows else None
    return {
        "found": node is not None,
        "node": node,
        "steps": steps,
        "elapsed_ms": res.result.elapsed_ms,
        "query_count": 1,
    }


def run_maintainer_contagion(
    client: HydraDBClient,
    developer: str,
    max_hops: int = MAX_HOPS,
    lens: Lens = SUPPLY_CHAIN,
) -> dict:
    step = QueryStep(
        f"MATCH (d:{lens.developer_node} {{handle: $dev}})<-[:{lens.maintains_rel}]-"
        f"(p:{lens.version_node}) "
        "RETURN DISTINCT p.name AS name, p.id AS id",
        {"dev": developer},
        f"packages maintained by {developer}",
    )
    res = execute(client, [step])[0]
    packages = sorted({r["name"] for r in res.result.rows})
    return {
        "found": bool(packages),
        "developer": developer,
        "packages": packages,
        "steps": [(step, res)],
        "elapsed_ms": res.result.elapsed_ms,
        "query_count": 1,
    }


def _score_nearest(seed_names: list[str]) -> dict[str, float]:
    ratios: dict[str, float] = {}
    for name in dict.fromkeys(seed_names):
        ratios[name] = 1.0

    def nearest(candidate: str) -> float:
        return max(difflib.SequenceMatcher(None, candidate, s).ratio() for s in ratios)

    return nearest


def run_typosquat_candidates(
    client: HydraDBClient,
    seed_names: list[str] | None = None,
    top_k: int = 15,
    lens: Lens = SUPPLY_CHAIN,
) -> dict:
    steps: list = []
    seeds: list[str] = list(seed_names or [])
    if not seeds:
        s = plan_popular_packages(lens)
        r = execute(client, [s])[0]
        steps.append((s, r))
        seeds = [row["name"] for row in r.result.rows]
    s = plan_typosquat_candidates(since=int(time.time()) - 120 * 86400, lens=lens)
    r = execute(client, [s])[0]
    steps.append((s, r))
    if not seeds or not r.result.rows:
        return {
            "found": False,
            "candidates": [],
            "steps": steps,
            "elapsed_ms": total_elapsed([x for _, x in steps]),
        }
    nearest = _score_nearest(seeds)
    scored: list[dict] = []
    for row in r.result.rows:
        score = nearest(row["name"])
        if score >= 0.60:
            scored.append(
                {
                    "id": row["id"],
                    "name": row["name"],
                    "score": round(score, 3),
                    "published_at": row["published_at"],
                    "deprecated": row["deprecated"],
                    "nearest_seed": max(
                        seeds,
                        key=lambda s_: difflib.SequenceMatcher(
                            None, row["name"], s_
                        ).ratio(),
                    ),
                }
            )
    for cand in scored:
        s = plan_in_degree(cand["id"], lens)
        r = execute(client, [s])[0]
        steps.append((s, r))
        cand["in_degree"] = r.result.rows[0]["degree"]
    for cand in scored:
        orphan = 0.15 if cand["in_degree"] == 0 else 0.0
        dep = 0.10 if cand["deprecated"] else 0.0
        cand["typosquat_score"] = round(cand["score"] + orphan + dep, 3)
    scored.sort(key=lambda x: (-x["typosquat_score"], -x["published_at"]))
    top = scored[:top_k]
    return {
        "found": bool(top),
        "seeds": seeds,
        "candidates": top,
        "steps": steps,
        "elapsed_ms": total_elapsed([x for _, x in steps]),
        "query_count": len(steps),
    }


def run_fetch_subgraph(
    client: HydraDBClient, node_id: int, depth: int = 2, lens: Lens = SUPPLY_CHAIN
) -> dict:
    steps: list = []
    nodes: dict[int, dict] = {}

    def absorb(rows: list[dict], via: str) -> None:
        for row in rows:
            if row.get("id") is None:
                continue
            nid = int(row["id"])
            nodes.setdefault(
                nid,
                {
                    "id": nid,
                    "name": row.get("name"),
                    "version": row.get("version"),
                    "via": via,
                },
            )

    for s in (plan_subgraph_out(node_id, depth, lens), plan_subgraph_in(node_id, lens)):
        r = execute(client, [s])[0]
        steps.append((s, r))
        absorb(r.result.rows, s.purpose)
    edges: list[dict] = []
    for s, r in steps:
        if "subgraph" in s.purpose:
            for row in r.result.rows:
                if row.get("id") is not None:
                    edges.append(
                        {"src": node_id, "dst": int(row["id"]), "type": "DEPENDS_ON"}
                    )
        else:
            for row in r.result.rows:
                if row.get("id") is not None:
                    edges.append(
                        {"src": int(row["id"]), "dst": node_id, "type": "DEPENDS_ON"}
                    )
    return {
        "node_id": node_id,
        "nodes": list(nodes.values()),
        "edges": edges,
        "steps": steps,
        "elapsed_ms": total_elapsed([x for _, x in steps]),
        "query_count": len(steps),
    }

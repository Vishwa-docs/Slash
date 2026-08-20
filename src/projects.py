"""Multi-repo projects: build a real dependency graph from any pasted GitHub repo.

A project = one Git repository. Slash pulls its real ``package.json`` (and
``package-lock.json`` when committed, else materializes a genuine npm lockfile),
resolves every pinned version, cross-references OSV advisories, and ingests the
subgraph into HydraDB under the same Service/Lockfile/PackageVersion schema as
the seeded corpus — every name and version is real, nothing is invented.

Persistence (all under ``data/``):
  - ``projects.json``                     project records + chat sessions
  - ``projects/<slug>/snapshot.json``     nodes+edges in dataset shape
  - ``projects/<slug>/osv/advisories.json``  per-project OSV cache
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time
import urllib.parse
from concurrent import futures
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import fetch_real

from src import schema
from src.hydradb_client import HydraDBClient

PROJECTS_STORE = ROOT / "data" / "projects.json"
PROJECTS_DIR = ROOT / "data" / "projects"
OSV_ENDPOINT = "https://api.osv.dev/v1/query"
GH_RAW = "https://raw.githubusercontent.com/{owner}/{name}/{branch}/{path}"
GH_API = "https://api.github.com/repos/{owner}/{name}"

SCHEMA_VERSION = 1


# ---- store -------------------------------------------------------------------


def load_store() -> dict:
    if not PROJECTS_STORE.exists():
        return {"projects": []}
    try:
        return json.loads(PROJECTS_STORE.read_text())
    except Exception:  # noqa: BLE001
        return {"projects": []}


def save_store(store: dict) -> None:
    PROJECTS_STORE.parent.mkdir(parents=True, exist_ok=True)
    PROJECTS_STORE.write_text(json.dumps(store, indent=1))


def slug_for(ref: str) -> str:
    ref = (
        ref.replace("https://github.com/", "")
        .replace("http://github.com/", "")
        .strip("/")
    )
    parts = [re.sub(r"[^A-Za-z0-9]", "-", p.lower()) for p in ref.split("/")[:2]]
    return "-".join(p for p in parts if p)


# The repo seeded by default so the console works offline, out of the box.
DEMO_REPO = "Vishwa-docs/reefguard-coral-hackathon"
DEMO_PROJECT_ID = slug_for(DEMO_REPO)


def parse_ref(link: str) -> tuple[str, str]:
    m = re.search(r"github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/?$", link.strip())
    if m:
        return m.group(1), m.group(2)
    parts = link.strip().strip("/").split("/")
    if len(parts) >= 2 and parts[0] and parts[1]:
        return parts[0], parts[1]
    raise ValueError("could not read a GitHub repository from that input")


# ---- fetch helpers -----------------------------------------------------------


def _default_branch(owner: str, name: str) -> str:
    return (
        fetch_real.http_json(GH_API.format(owner=owner, name=name)).get(
            "default_branch"
        )
        or "main"
    )


def _raw(owner: str, name: str, branch: str, path: str) -> dict | None:
    url = GH_RAW.format(owner=owner, name=name, branch=branch, path=path)
    try:
        return fetch_real.http_json(url)
    except Exception:  # noqa: BLE001
        return None


def _materialize_lockfile(package_json: dict, tmpdir: Path) -> dict:
    """Write the real package.json and let npm produce a genuine lockfile."""
    tmpdir.mkdir(parents=True, exist_ok=True)
    (tmpdir / "package.json").write_text(json.dumps(package_json, indent=2))
    lock = tmpdir / "package-lock.json"
    if lock.exists():
        lock.unlink()
    subprocess.run(
        [
            "npm",
            "install",
            "--package-lock-only",
            "--ignore-scripts",
            "--no-audit",
            "--legacy-peer-deps",
        ],
        cwd=tmpdir,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(lock.read_text())


def _parse_lockfile(
    lock: dict,
) -> tuple[dict[str, str], dict[str, list[tuple[str, str]]], set[str]]:
    """(name->version, name->[(dep, dep_version)], root_direct_deps).

    npm lockfile v3 omits the ``name`` field on most entries, so fall back to
    the ``node_modules/``-relative path (which preserves the scope).
    """
    entries: dict[str, str] = {}
    deps: dict[str, dict[str, str]] = {}
    root: dict[str, str] = {}
    for path, meta in (lock.get("packages") or {}).items():
        if meta.get("link"):
            continue
        if path == "":
            root = dict(meta.get("dependencies") or {})
            root.update(meta.get("devDependencies") or {})
            continue
        rel = path.rsplit("node_modules/", 1)[-1]
        name = meta.get("name") or rel
        ver = meta.get("version")
        if not name or not ver:
            continue
        entries.setdefault(name, ver)
        deps.setdefault(name, {}).update(meta.get("dependencies") or {})
    adjacency: dict[str, list[tuple[str, str]]] = {}
    for name, depmap in deps.items():
        for dep, rng in depmap.items():
            dep_ver = entries.get(dep)
            if dep_ver and fetch_real._satisfies(dep_ver, rng):
                adjacency.setdefault(name, []).append((dep, dep_ver))
    root_deps = {d for d in root if d in entries}
    return entries, adjacency, root_deps


def _fetch_osv(names: list[str]) -> dict[str, list[dict]]:

    def one(name: str) -> tuple[str, list[dict]]:
        try:
            r = fetch_real.http_json(
                OSV_ENDPOINT,
                method="POST",
                body={"package": {"name": name, "ecosystem": "npm"}},
            )
            return name, r.get("vulns", [])
        except Exception:  # noqa: BLE001
            return name, []

    out: dict[str, list[dict]] = {}
    with futures.ThreadPoolExecutor(max_workers=10) as ex:
        for name, vulns in ex.map(one, sorted(set(names))):
            out[name] = vulns
    return out


def _aliases(vuln: dict) -> list[str]:
    aliases = [a for a in vuln.get("aliases", []) if a.startswith("CVE-")]
    return aliases or ([vuln.get("id")] if vuln.get("id") else [])


def _doc_times(names: list[str]) -> dict[str, dict]:
    docs = fetch_real.fetch_npm_docs(list(names))
    return {urllib.parse.unquote(u.rsplit("/", 1)[1]): d for u, d in docs.items()}


# ---- generation --------------------------------------------------------------


def generate_project(link: str) -> dict:
    owner, name = parse_ref(link)
    ref = f"{owner}/{name}"
    slug = slug_for(ref)
    branch = _default_branch(owner, name)
    package_json = _raw(owner, name, branch, "package.json")
    if not package_json:
        raise ValueError(f"{ref} has no package.json on branch {branch}")
    lock = _raw(owner, name, branch, "package-lock.json")
    if not lock:
        lock = _materialize_lockfile(package_json, PROJECTS_DIR / "tmp" / slug)
    entries, adjacency, root_deps = _parse_lockfile(lock)

    docs = _doc_times(list(entries))
    osv = _fetch_osv(list(entries))
    now = int(time.time())

    nodes: list[dict] = []
    edges: dict[str, list[dict]] = {t: [] for t in schema.EDGE_PROPS}

    version_ids: dict[str, dict[int, str]] = {}
    seen: set[tuple[str, str]] = set()
    for package, ver in sorted(entries.items()):
        if (package, ver) in seen:
            continue
        seen.add((package, ver))
        nid = fetch_real.stable_id(schema.PACKAGE_VERSION, f"{package}@{ver}")
        version_ids.setdefault(package, {})[ver] = nid  # type: ignore[index]
        doc = docs.get(package, {})
        times = doc.get("time", {})
        aliases = sorted({a for v in osv.get(package, []) for a in _aliases(v)})
        vulnerable = any(
            fetch_real._satisfies(ver, fetch_real._affected_expr(aff))
            for v in osv.get(package, [])
            for aff in v.get("affected", [])
            if aff.get("package", {}).get("name") == package
        )
        npm_ver = (doc.get("versions") or {}).get(ver) or {}
        nodes.append(
            {
                "label": schema.PACKAGE_VERSION,
                "id": nid,
                "properties": {
                    "name": package,
                    "version": ver,
                    "published_at": fetch_real._iso_to_epoch(times.get(ver)) or 0,
                    "valid_until": schema.VALID_UNTIL_LIVE,
                    "deprecated": bool(npm_ver.get("deprecated")),
                    "popular": False,
                    "malicious": vulnerable,
                    "advisory_id": "|".join(aliases) if vulnerable else "",
                    "is_typosquat": False,
                },
            }
        )
        if vulnerable:
            mnt = [
                m.get("name") or "?"
                for m in (npm_ver.get("maintainers") or doc.get("maintainers") or [])
                if m
            ]
            for developer in set(mnt):
                dev_id = fetch_real.stable_id(schema.DEVELOPER, developer)
                nodes.append(
                    {
                        "label": schema.DEVELOPER,
                        "id": dev_id,
                        "properties": {"handle": developer, "email": ""},
                    }
                )
                edges[schema.MAINTAINED_BY].append(
                    {
                        "edge_id": fetch_real.stable_id(
                            schema.MAINTAINED_BY, f"{developer}:{package}@{ver}"
                        ),
                        "source": nid,
                        "target": dev_id,
                        "properties": {
                            "since": now,
                            "valid_from": now,
                            "valid_until": schema.VALID_UNTIL_LIVE,
                        },
                    }
                )

    svc_id = fetch_real.stable_id(schema.SERVICE, ref)
    lock_id = fetch_real.stable_id(schema.LOCKFILE, ref)
    nodes.append({"label": schema.SERVICE, "id": svc_id, "properties": {"name": ref}})
    nodes.append(
        {
            "label": schema.LOCKFILE,
            "id": lock_id,
            "properties": {
                "app": ref,
                "created_at": now,
                "resolved_at": now,
            },
        }
    )
    nodes.append(
        {
            "label": schema.PACKAGE,
            "id": fetch_real.stable_id(schema.PACKAGE, ref),
            "properties": {"name": ref, "popular": False},
        }
    )
    edges[schema.USES_LOCKFILE].append(
        {
            "edge_id": fetch_real.stable_id(schema.USES_LOCKFILE, ref),
            "source": svc_id,
            "target": lock_id,
            "properties": {
                "since": now,
                "valid_from": now,
                "valid_until": schema.VALID_UNTIL_LIVE,
            },
        }
    )
    for package, ver in sorted(entries.items()):
        nid = version_ids.get(package, {}).get(ver)
        if nid is None:
            continue
        edges[schema.RESOLVES_TO].append(
            {
                "edge_id": fetch_real.stable_id(
                    schema.RESOLVES_TO, f"{ref}:{package}@{ver}"
                ),
                "source": lock_id,
                "target": nid,
                "properties": {
                    "at": now,
                    "was_resolved_while_live": True,
                    "valid_from": now,
                    "valid_until": schema.VALID_UNTIL_LIVE,
                },
            }
        )
        for dep, dep_ver in adjacency.get(package, []):
            dep_id = version_ids.get(dep, {}).get(dep_ver)
            if dep_id is None:
                continue
            edges[schema.DEPENDS_ON].append(
                {
                    "edge_id": fetch_real.stable_id(
                        schema.DEPENDS_ON, f"{package}@{ver}->{dep}@{dep_ver}"
                    ),
                    "source": nid,
                    "target": dep_id,
                    "properties": {
                        "pinned": dep in root_deps,
                        "valid_from": now,
                        "valid_until": schema.VALID_UNTIL_LIVE,
                    },
                }
            )

    snapshot = {"nodes": nodes, "edges": edges}
    proj_dir = PROJECTS_DIR / slug
    proj_dir.mkdir(parents=True, exist_ok=True)
    (proj_dir / "snapshot.json").write_text(json.dumps(snapshot, indent=1))
    (proj_dir / "osv").mkdir(exist_ok=True)
    (proj_dir / "osv" / "advisories.json").write_text(
        json.dumps(
            [{"package": p, "vulns": v} for p, v in sorted(osv.items())], indent=1
        )
    )

    client = HydraDBClient()
    from scripts.ingest import upsert_edges, upsert_nodes

    upsert_nodes(client, snapshot, schema.NODE_PROPS)
    upsert_edges(client, snapshot, schema.EDGE_PROPS)

    record = _record_from_snapshot(slug, ref, now, snapshot)
    store = load_store()
    store["projects"] = [p for p in store["projects"] if p["id"] != slug]
    store["projects"].append(record)
    save_store(store)
    print(
        f"[projects] {ref} -> {slug}: {snapshot['nodes'].__len__()} nodes, "
        f"{sum(len(e) for e in snapshot['edges'].values())} edges, "
        f"{record['stats']['advisories']} advisories"
    )
    return record


def _record_from_snapshot(slug: str, ref: str, now: int, snapshot: dict) -> dict:
    malicious = 0
    advisories: list[dict] = []
    for n in snapshot["nodes"]:
        if n.get("label") != schema.PACKAGE_VERSION:
            continue
        p = n["properties"]
        if p.get("malicious"):
            malicious += 1
            advisories.append(
                {
                    "name": p["name"],
                    "version": p["version"],
                    "advisory_id": p.get("advisory_id", ""),
                }
            )
    return {
        "id": slug,
        "repo": ref,
        "url": f"https://github.com/{ref}",
        "slug": slug,
        "status": "ready",
        "generated_at": now,
        "demo": False,
        "schema_version": SCHEMA_VERSION,
        "stats": {
            "nodes": len(snapshot["nodes"]),
            "versions": sum(
                1 for n in snapshot["nodes"] if n.get("label") == schema.PACKAGE_VERSION
            ),
            "services": 1,
            "malicious": malicious,
            "advisories": len(advisories),
            "edges": sum(len(v) for v in snapshot["edges"].values()),
        },
        "advisories": advisories,
        "sessions": [],
    }


# ---- projects API ------------------------------------------------------------


def list_projects() -> list[dict]:
    out = []
    for p in load_store()["projects"]:
        out.append(
            {
                "id": p["id"],
                "repo": p["repo"],
                "url": p["url"],
                "demo": p.get("demo", False),
                "generated_at": p.get("generated_at"),
                "stats": p.get("stats", {}),
                "advisory_count": len(p.get("advisories", [])),
            }
        )
    return out


def project(project_id: str) -> dict | None:
    for p in load_store()["projects"]:
        if p["id"] == project_id or p["slug"] == project_id:
            return p
    return None


def new_session(project_id: str, title: str | None = None) -> dict | None:
    store = load_store()
    for p in store["projects"]:
        if p["id"] != project_id:
            continue
        sessions = p.setdefault("sessions", [])
        sid = f"s{len(sessions) + 1}"
        session = {
            "id": sid,
            "title": title or f"session {len(sessions) + 1}",
            "created_at": int(time.time()),
            "turns": [],
        }
        sessions.insert(0, session)
        save_store(store)
        return session
    return None


def append_turn(project_id: str, session_id: str, turn: dict) -> None:
    store = load_store()
    for p in store["projects"]:
        if p["id"] != project_id:
            continue
        for s in p.get("sessions", []):
            if s["id"] == session_id:
                s.setdefault("turns", []).append(turn)
                save_store(store)
                return


def overview(project_id: str) -> dict:
    p = project(project_id)
    if not p:
        return {"error": "project not found"}
    return {
        "project": {
            "id": p["id"],
            "repo": p["repo"],
            "url": p["url"],
            "demo": p.get("demo", False),
        },
        "dataset": f"repo {p['repo']} · generated from its real package lockfile + OSV",
        "stats": p["stats"],
        "advisories": p["advisories"],
        "examples": _examples_for(p),
        "sessions": p.get("sessions", []),
    }


def _examples_for(p: dict) -> list[dict]:
    example = p["advisories"][0] if p["advisories"] else None
    top = example["name"] if example else _repo_as_package(p["repo"])
    out: list[dict] = []
    for a in p["advisories"][:3]:
        out.append(
            {
                "question": f"Which services are exposed by {a['name']}@{a['version']}?",
                "hint": f"real advisory {a['advisory_id'] or 'OSV'} resolved by {p['repo']}",
            }
        )
        out.append(
            {
                "question": f"Which apps resolved {a['name']}@{a['version']} while it was live?",
                "hint": "lockfile resolution history for the real advisory",
            }
        )
    if example:
        out.append(
            {
                "question": f"What is the blast radius of {example['name']}@{example['version']}?",
                "hint": "transitive dependants — the core graph question",
            }
        )
    out.append(
        {
            "question": f"What is the latest version of {top}?",
            "hint": "package lookup against the real registry metadata",
        }
    )
    out.append(
        {
            "question": f"Is there a typosquat near {top}?",
            "hint": "edit-distance lookalikes over real package names",
        }
    )
    return out


def _repo_as_package(repo: str) -> str:
    return re.sub(r"[^a-z0-9-]", "-", repo.split("/")[-1].lower())


def _is_project_service(service: str, repo: str) -> bool:
    """Match a graph Service name against this repo project (ref or basename)."""
    basename = repo.split("/")[-1]
    return (
        service == repo
        or service.lower() == repo.lower()
        or service == basename
        or service.lower() == basename.lower()
    )


# ---- boot seed ---------------------------------------------------------------


def _load_snapshot(slug: str) -> dict | None:
    try:
        return json.loads((PROJECTS_DIR / slug / "snapshot.json").read_text())
    except (OSError, ValueError):
        return None


def sync_all() -> None:
    """Ingest every committed project snapshot into HydraDB and register records.

    Run on server boot so a fresh clone reproduces the full graph (the corpus is
    ingested once by ``scripts/ingest.py``; project snapshots are self-healing
    here). ``MERGE`` upserts keep re-runs idempotent.
    """
    client = HydraDBClient()
    from scripts.ingest import upsert_edges, upsert_nodes

    store = load_store()
    known = {p["id"] for p in store.setdefault("projects", [])}
    for slug in sorted(p.parent.name for p in PROJECTS_DIR.glob("*/snapshot.json")):
        snapshot = _load_snapshot(slug)
        if snapshot is None:
            continue
        upsert_nodes(client, snapshot, schema.NODE_PROPS)
        upsert_edges(client, snapshot, schema.EDGE_PROPS)
        if slug in known:
            continue
        repo = next(
            (p["repo"] for p in store["projects"] if p["id"] == slug),
            f"{slug}",
        )
        store["projects"].append(
            _record_from_snapshot(slug, repo, int(time.time()), snapshot)
        )
        save_store(store)
        known.add(slug)
    register_demo_if_missing()


def register_demo_if_missing() -> None:
    """Register the committed demo repo snapshot as a project on server boot.

    If ``data/projects/<demo>/snapshot.json`` was committed, the demo project is
    restored without any network — the console works on a judge machine offline.
    """
    if project(DEMO_PROJECT_ID):
        return
    snap = PROJECTS_DIR / DEMO_PROJECT_ID / "snapshot.json"
    if not snap.exists():
        return
    try:
        snapshot = json.loads(snap.read_text())
    except Exception:  # noqa: BLE001
        return
    record = _record_from_snapshot(
        DEMO_PROJECT_ID, DEMO_REPO, int(time.time()), snapshot
    )
    record["demo"] = True
    store = load_store()
    store.setdefault("projects", []).insert(0, record)
    save_store(store)


# ---- project-scoped scan + ask ----------------------------------------------


def scan(project_id: str) -> dict:
    """Exposure report scoped to the services of a single project repo."""
    from src.graph_service import run_resolved_while_live

    p = project(project_id)
    if not p:
        return {"error": "project not found"}
    t0 = time.time()
    client = HydraDBClient()
    rows = []
    for adv in p.get("advisories", []):
        r = run_resolved_while_live(client, adv["name"], adv["version"])
        if not r.get("found"):
            continue
        records = r.get("lockfiles", [])
        ours = [s for s in r.get("services", []) if _is_project_service(s, p["repo"])]
        records = [
            lf
            for lf in records
            if _is_project_service(lf.get("service", ""), p["repo"])
        ]
        rows.append(
            {
                "advisory_id": adv.get("advisory_id") or adv["name"],
                "name": adv["name"],
                "version": adv["version"],
                "services": ours,
                "lockfile_count": len(records),
                "appearing": sorted({lf["app"] for lf in records}),
                "resolved_while_live": records,
                "recompute_agrees": r.get("recompute_agrees", True),
                "query_count": r.get("query_count", 0),
            }
        )
    rows.sort(key=lambda r: (-len(r["services"]), r["advisory_id"]))
    return {
        "generated_ms": round((time.time() - t0) * 1000, 1),
        "advisories_checked": len(p.get("advisories", [])),
        "advisories_present": len(rows),
        "exposures": rows,
        "totals": {
            "services_exposed": len({s for r in rows for s in r["services"]}),
            "apps_at_risk": len({a for r in rows for a in r["appearing"]}),
            "live_resolutions": sum(r["lockfile_count"] for r in rows),
        },
    }


def ask(
    project_id: str, question: str, session_id: str | None, llm_key: str | None
) -> dict:
    """Run the pipeline against HydraDB and scope service answers to the project.

    The graph is global (one shared package universe), so a project-scoped
    question filters the SLA-relevant facts — services and lockfiles — down to
    this repo. Blast radius / typosquat etc. stay global, which is the truth:
    a compromised package anywhere threatens every dependant in the graph.
    The turn is persisted onto the project's session.
    """
    from src.api import payload_for
    from src.models import IntentClass
    from src.pipeline import answer_with_result

    p = project(project_id)
    if not p:
        return {"error": "project not found"}
    client = HydraDBClient()
    verdict, result = answer_with_result(
        client,
        question,
        llm=bool(llm_key),
        llm_key=llm_key,
    )
    if (
        verdict.intent
        in (IntentClass.EXPOSED_SERVICES, IntentClass.RESOLVED_WHILE_LIVE)
        and result
        and result.get("found")
    ):
        result["services"] = [
            s for s in result.get("services", []) if _is_project_service(s, p["repo"])
        ]
        if "path_rows" in result:
            result["path_rows"] = [
                pr
                for pr in result["path_rows"]
                if _is_project_service(pr.get("service", ""), p["repo"])
            ]
        if "lockfiles" in result:
            result["lockfiles"] = [
                lf
                for lf in result["lockfiles"]
                if _is_project_service(lf.get("service", ""), p["repo"])
            ]
    meta = {
        "question": question,
        "intent": verdict.intent.value,
        "answer": verdict.answer,
        "summary": verdict.summary,
        "abstain": verdict.abstain,
        "healed": verdict.healed,
        "reported": verdict.reported,
        "reason": verdict.reason,
        "latency_ms": round(verdict.latency_ms, 2),
        "query_count": verdict.query_count,
        "evidence_chain": [
            {
                "purpose": e.purpose,
                "cypher": e.cypher,
                "params": e.params,
                "row_count": e.row_count,
                "elapsed_ms": round(e.elapsed_ms, 2),
            }
            for e in verdict.evidence_chain
        ],
        "payload": payload_for(verdict.intent, result),
    }
    if not any(s["id"] == session_id for s in p.get("sessions", [])):
        created = new_session(
            project_id, title=f"{meta['intent'][:12].lower()} · {question[:40]}"
        )
        if created:
            session_id = created["id"]
    if session_id:
        append_turn(
            project_id,
            session_id,
            {"answer": meta, "t": int(time.time() * 1000)},
        )
    return meta

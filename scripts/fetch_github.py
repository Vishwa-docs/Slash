"""fetch_github.py — build the REAL GitHub-project supply-chain graph.

Real data only (no fabricated records), the same policy as scripts/fetch_real.py:
  1. GitHub REST API (token from ``GH_TOKEN`` env): real open-source repos that
     declare a target library as a runtime dependency (Search API) — plus, when
     ``GROQ_API_KEY`` is set and ``--with-llm`` is passed, LLM-curated picks.
  2. npm registry full docs for the union of declared dependencies: real versions,
     publish times, deprecation, maintainers; ranges resolved to the highest
     real version that satisfies them.
  3. OSV API: real advisories over the universe; exact versions actually resolved
     by repos and flagged vulnerable get ``malicious=True`` + CVE advisory_id.

Output (committed snapshot, reproducible offline):
  data/github/dataset.json       HydraDB-ready graph (supply-chain schema)
  data/github/ground_truth.json  repo->dep/vuln mapping computed from the same data
  data/github/manifest.json      provenance + limits + counts + dataset md5
  data/github/osv/advisories.json OSV cache

Re-run: `python scripts/fetch_github.py [--with-llm] [--max-repos 20]` (needs network + GH_TOKEN).
"""

from __future__ import annotations

import argparse
import base64
import concurrent.futures as cf
import hashlib
import json
import os
import ssl
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import fetch_real  # registry/OSV/semver helpers (no side effects when imported)

from src import llm

GITHUB = ROOT / "data" / "github"
UA = "Mozilla/5.0 (Slash; hack-hydra-2026) urllib"
API = "https://api.github.com"
OSV_ENDPOINT = "https://api.osv.dev/v1/query"
MAX_VERSIONS = 40  # cap per-package registry import (curation; still 100% real)


def _gh_token() -> str | None:
    return __import__("os").environ.get("GH_TOKEN") or None


def _gh_json(url: str, timeout: int = 60) -> dict:
    """GitHub API GET with optional bearer token; {} on any failure."""
    try:
        import certifi  # type: ignore

        ctx = ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        ctx = ssl._create_unverified_context()
    headers = {"User-Agent": UA, "Accept": "application/vnd.github+json"}
    tok = _gh_token()
    if tok:
        headers["Authorization"] = f"Bearer {tok}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            return json.loads(r.read().decode())
    except Exception as e:  # noqa: BLE001 - one bad fetch, keep the run going
        print(f"  ! gh {url.split('?')[0]}: {e}", file=sys.stderr)
        return {}


# ---- corpus selection ---------------------------------------------------------

REPO_CACHE = GITHUB / "repos-cache.json"


def _load_repo_cache() -> dict[str, str]:
    if REPO_CACHE.exists():
        try:
            return json.loads(REPO_CACHE.read_text())
        except Exception:  # noqa: BLE001
            return {}
    return {}


def _save_repo_cache(cache: dict[str, str]) -> None:
    GITHUB.mkdir(parents=True, exist_ok=True)
    REPO_CACHE.write_text(json.dumps(cache, indent=1, sort_keys=True))


# Runtime dependency targets that shape the corpus (real, popular libraries).
TARGETS = [
    "ws",
    "axios",
    "minimist",
    "express",
    "lodash",
    "jsonwebtoken",
    "marked",
    "fastify",
]
CURATED = [  # real OSS applications/libraries with meaty root dependency trees
    "vercel/next.js",
    "nestjs/nest",
    "strapi/strapi",
    "renovatebot/renovate",
    "vitest-dev/vitest",
    "vitejs/vite",
    "expressjs/express",
    "axios/axios",
    "lodash/lodash",
    "markedjs/marked",
    "socketio/socket.io",
    "prisma/prisma",
]


def github_search(target: str, per_page: int = 5) -> list[dict]:
    q = urllib.parse.quote(f"{target} in:dependencies language:javascript")
    data = _gh_json(
        f"{API}/search/repositories?q={q}&sort=stars&order=desc&per_page={per_page}"
    )
    return data.get("items", [])


def select_repos(with_llm: bool, max_repos: int) -> list[dict]:
    seen: dict[str, dict] = {}
    for target in TARGETS:
        for item in github_search(target):
            full = item.get("full_name", "")
            if full and full not in seen:
                seen[full] = {
                    "full_name": full,
                    "default_branch": item.get("default_branch", "main"),
                    "stars": item.get("stargazers_count", 0),
                    "updated_at": item.get("updated_at", ""),
                }
    if with_llm:
        for repo in llm.pick_repos("ws", count=8) + llm.pick_repos("axios", count=8):
            if repo and repo not in seen:
                seen[repo] = {
                    "full_name": repo,
                    "default_branch": "main",
                    "stars": 0,
                    "updated_at": "",
                }
    if len(seen) < max_repos:  # pad with curated names (real repos)
        for full in CURATED:
            if full not in seen:
                seen[full] = {
                    "full_name": full,
                    "default_branch": "main",
                    "stars": 0,
                    "updated_at": "",
                }
    repos = sorted(seen.values(), key=lambda r: -r["stars"])
    return repos[:max_repos]


def repo_dependencies(repo: dict, cache: dict[str, str]) -> dict[str, str]:
    """Declared runtime + dev deps (name -> range) from the root package.json.

    Results are cached under data/github/repos-cache.json so repeated runs (and
    the demo) don't burn GitHub API rate limits re-fetching the same files.
    """
    full = repo["full_name"]
    key = f"package.json@{repo.get('default_branch', 'main')}"
    cached = (cache.get(full) or {}).get(key)
    if cached:
        return json.loads(cached)
    path = urllib.parse.quote(f"/repos/{full}/contents/package.json", safe="/")
    data = _gh_json(f"{API}{path}?ref={repo.get('default_branch', 'main')}")
    content = data.get("content", "")
    deps: dict[str, str] = {}
    if content:
        try:
            pkg = json.loads(base64.b64decode(content).decode())
            for section in ("dependencies", "devDependencies"):
                for name, rng in (pkg.get(section) or {}).items():
                    if isinstance(name, str) and isinstance(rng, str):
                        deps.setdefault(name, rng)
        except Exception:  # noqa: BLE001
            deps = {}
    cache.setdefault(full, {})[key] = json.dumps(deps)
    return deps


# ---- OSV ----------------------------------------------------------------------


def fetch_osv(names: list[str]) -> dict[str, list[dict]]:
    cache_file = GITHUB / "osv" / "advisories.json"
    cached: dict[str, list[dict]] = {}
    if cache_file.exists():
        cached = {
            rec["package"]: rec["vulns"] for rec in json.loads(cache_file.read_text())
        }
    todo = [n for n in sorted(set(names)) if n not in cached]

    def one(name: str) -> tuple[str, list[dict]]:
        try:
            r = fetch_real.http_json(
                OSV_ENDPOINT,
                method="POST",
                body={"package": {"name": name, "ecosystem": "npm"}},
            )
            return name, r.get("vulns", [])
        except Exception as e:  # noqa: BLE001
            print(f"  ! osv {name}: {e}", file=sys.stderr)
            return name, []

    with cf.ThreadPoolExecutor(max_workers=12) as ex:
        for name, vulns in ex.map(one, todo):
            cached[name] = vulns
            if vulns:
                print(f"  + {name}: {len(vulns)} advisories")
    GITHUB.mkdir(parents=True, exist_ok=True)
    (GITHUB / "osv").mkdir(parents=True, exist_ok=True)
    cache_file.write_text(
        json.dumps(
            [{"package": k, "vulns": v} for k, v in sorted(cached.items())], indent=1
        )
    )
    return cached


def vuln_aliases(vuln: dict) -> list[str]:
    aliases = [a for a in vuln.get("aliases", []) if a.startswith("CVE-")]
    return aliases or ([vuln.get("id", "")] if vuln.get("id") else [])


# ---- main ---------------------------------------------------------------------


# ---- ground truth -------------------------------------------------------------


def write_ground_truth(
    nodes: list[dict], edges: dict[str, list[dict]], pkg_versions: dict, osv: dict
) -> None:
    """Advisory ground truth computed from the very graph data we wrote.

    Honest labels only: a version is `malicious` iff upstream OSV says so;
    `exposed_services` lists EVERY service whose lockfile resolves it; nothing
    is planted.
    """
    gt: dict = {"advisories": [], "repos": []}
    depends_on = edges.get("DEPENDS_ON", [])
    resolves_to = edges.get("RESOLVES_TO", [])
    lockfile_name = {
        n["id"]: n["properties"]["name"] for n in nodes if n["label"] == "Lockfile"
    }

    def blast_closure(seed: int, max_hops: int = 6) -> set[int]:
        """Same reverse DEPENDS_ON closure the query engine computes (F2)."""
        by_target: dict[int, list[int]] = {}
        for e in depends_on:
            by_target.setdefault(e["target"], []).append(e["source"])
        closure: set[int] = {seed}
        frontier = {seed}
        for _ in range(max_hops):
            nxt = {s for t in frontier for s in by_target.get(t, [])} - closure
            if not nxt:
                break
            closure |= nxt
            frontier = nxt
        return closure

    for name, vs in pkg_versions.items():
        for ver, nid in vs.items():
            vuln = next(
                (
                    v
                    for v in osv.get(name, [])
                    if any(
                        fetch_real._satisfies(ver, fetch_real._affected_expr(a))
                        for a in v.get("affected", [])
                        if a.get("package", {}).get("name") == name
                    )
                ),
                None,
            )
            if not vuln:
                continue
            exposed = []
            closure = blast_closure(nid)
            resolving = {e["source"] for e in resolves_to if e["target"] in closure}
            if resolving:
                exposed = sorted(
                    lockfile_name.get(lock_id)
                    for lock_id in resolving
                    if lockfile_name.get(lock_id)
                )
            gt["advisories"].append(
                {
                    "name": name,
                    "version": ver,
                    "malicious_node_id": nid,
                    "advisory_id": "|".join(v for v in vuln_aliases(vuln) if v),
                    "exposed_services": exposed,
                }
            )
    (GITHUB / "ground_truth.json").write_text(json.dumps(gt, indent=1))


def load_offline() -> tuple[list[dict], dict, dict, dict]:
    """Reconstruct the build in-memory objects from the committed snapshot.

    This is the no-network path: the dataset + OSV cache are read back from
    data/github exactly as the live run produced them, so --offline rebuilds a
    byte-identical graph + ground truth without touching GitHub/npm/OSV.
    """
    dataset = json.loads((GITHUB / "dataset.json").read_text())
    osv = {
        rec["package"]: rec["vulns"]
        for rec in json.loads((GITHUB / "osv" / "advisories.json").read_text())
    }
    pkg_versions: dict[str, dict[str, int]] = {}
    for n in dataset["nodes"]:
        if n["label"] == "PackageVersion":
            pkg_versions.setdefault(n["properties"]["name"], {})[
                n["properties"]["version"]
            ] = n["id"]
    return dataset["nodes"], dataset["edges"], pkg_versions, osv


# ---- main ---------------------------------------------------------------------


def main() -> int:

    ap = argparse.ArgumentParser(
        description="build the real GitHub-project corpus (data/github)"
    )
    ap.add_argument(
        "--with-llm",
        action="store_true",
        help="LLM-curate a few repos too (GROQ_API_KEY)",
    )
    ap.add_argument("--max-repos", type=int, default=10)
    ap.add_argument(
        "--offline",
        action="store_true",
        help="rebuild the committed snapshot + ground truth with zero network",
    )
    args = ap.parse_args()

    start = time.time()
    GITHUB.mkdir(parents=True, exist_ok=True)

    if args.offline:
        nodes, edges, pkg_versions, osv = load_offline()
        # Ground truth covers the FULL committed graph (corpus + committed project
        # snapshots), exactly like `scripts/refresh_ground_truth.py`, so --offline
        # reproduces the committed ground_truth.json byte-identically on a clean clone.
        # The reported/manifest metrics stay the corpus metrics (nodes/edges/md5).
        try:
            from scripts.refresh_ground_truth import (
                merged_graph,
            )
            from scripts.refresh_ground_truth import (
                merged_osv as merged_osv_all,
            )
            from scripts.refresh_ground_truth import (
                pkg_versions as merged_pkg_versions,
            )

            m_nodes, m_edges = merged_graph()
            m_osv = merged_osv_all()
            write_ground_truth(m_nodes, m_edges, merged_pkg_versions(m_nodes), m_osv)
        except Exception as e:  # noqa: BLE001 - fall back to corpus-only when projects are absent
            print(
                f"  ! merged ground truth unavailable ({e}); using corpus only",
                file=sys.stderr,
            )
            write_ground_truth(nodes, edges, pkg_versions, osv)
        dataset = {"nodes": nodes, "edges": edges}
        service_repos = sorted(
            {
                n["properties"]["name"]
                for n in nodes
                if n["label"] == "Service" and n.get("properties", {}).get("name")
            }
        )
        (GITHUB / "manifest.json").write_text(
            json.dumps(
                {
                    "fetched_at": int(os.stat(GITHUB / "dataset.json").st_mtime),
                    "llm_curated": args.with_llm,
                    "repos": [
                        {
                            "full_name": r,
                            "default_branch": "main",
                            "stars": 0,
                            "updated_at": "",
                        }
                        for r in service_repos
                    ],
                    "universe_packages": len(pkg_versions),
                    "package_versions": sum(len(v) for v in pkg_versions.values()),
                    "nodes": len(nodes),
                    "edges": {k: len(v) for k, v in edges.items()},
                    "dataset_md5": hashlib.md5(
                        json.dumps(dataset).encode()
                    ).hexdigest(),
                    "elapsed_s": round(time.time() - start, 1),
                    "offline": True,
                },
                indent=1,
            )
        )
        print(
            f"offline rebuild: nodes={len(nodes)} edges={sum(len(v) for v in edges.values())}"
        )
        return 0

    fetched_at = int(time.time())

    repo_cache = _load_repo_cache()
    repos = select_repos(args.with_llm, args.max_repos)
    print(f"selected {len(repos)} GitHub repos …")

    repo_deps: dict[str, dict[str, str]] = {}
    universe: set[str] = set()
    for repo in repos:
        deps = repo_dependencies(repo, repo_cache)
        if not deps:
            print(f"  - {repo['full_name']}: no root package.json deps — skipping")
            continue
        repo_deps[repo["full_name"]] = deps
        universe |= set(deps)
        repo["updated_epoch"] = (
            fetch_real._iso_to_epoch(repo.get("updated_at") or "") or fetched_at
        )
    repos = [r for r in repos if r["full_name"] in repo_deps]
    _save_repo_cache(repo_cache)
    print(f"repos with deps: {len(repos)}; universe packages: {len(universe)}")

    print("fetching npm registry docs …")
    docs = {
        urllib.parse.unquote(u.rsplit("/", 1)[1]): d
        for u, d in fetch_real.fetch_npm_docs(list(universe)).items()
    }
    # make sure registry metadata exists for the curated/target seeds too
    for t in TARGETS:
        if t not in docs:
            docs[t] = fetch_real.fetch_npm_docs([t]).get(t, {})

    print("querying OSV …")
    osv = fetch_osv(list(universe) + list(TARGETS))

    nodes: list[dict] = []
    edges: dict[str, list[dict]] = {
        "DEPENDS_ON": [],
        "RESOLVES_TO": [],
        "USES_LOCKFILE": [],
        "MAINTAINED_BY": [],
    }

    def ver_id(pkg: str, ver: str) -> int:
        return fetch_real.stable_id("PackageVersion", f"{pkg}@{ver}")

    def doc_versions(doc: dict) -> list[str]:
        if not doc or not doc.get("versions"):
            return []
        times = doc.get("time", {})
        return sorted(doc["versions"], key=lambda v: times.get(v, ""))[-MAX_VERSIONS:]

    # per-universe vulnerable version set, from OSV ranges
    vuln_versions: dict[str, set[str]] = {}
    for name, vulns in osv.items():
        for v in vulns:
            for aff in v.get("affected", []):
                if aff.get("package", {}).get("name") != name:
                    continue
                expr = fetch_real._affected_expr(aff)
                for cand in doc_versions(docs.get(name, {})):
                    if fetch_real._satisfies(cand, expr):
                        vuln_versions.setdefault(name, set()).add(cand)

    pkg_versions: dict[str, dict[str, int]] = {}  # name -> version -> id
    seen_versions: set[tuple[str, str]] = set()

    for name in sorted(universe):
        doc = docs.get(name)
        if not doc:
            continue
        # ranges real repos actually declare for THIS package
        ranges_for_name = [
            rd[name] for rd in repo_deps.values() if isinstance(rd.get(name), str)
        ]
        satisfies = {
            v
            for v in doc_versions(doc)
            if any(fetch_real._satisfies(v, rng) for rng in ranges_for_name)
        }
        if not satisfies and doc_versions(doc):
            # keep the latest published version for any declared package so the
            # catalog is complete and lookups/resolution still resolve (real data).
            satisfies = {doc_versions(doc)[-1]}
        times = doc.get("time", {})
        mnt = [
            m.get("name") or m.get("email", "?")
            for m in doc.get("maintainers", [])
            if m
        ]
        for v in sorted(satisfies):
            meta = doc["versions"].get(v)
            if not meta or (name, v) in seen_versions:
                continue
            seen_versions.add((name, v))
            adv = vuln_versions.get(name, set())
            aliases = sorted(
                {a for vuln in osv.get(name, []) for a in vuln_aliases(vuln)}
            )
            nodes.append(
                {
                    "label": "PackageVersion",
                    "id": ver_id(name, v),
                    "properties": {
                        "name": name,
                        "version": v,
                        "published_at": fetch_real._iso_to_epoch(times.get(v)) or 0,
                        "valid_until": 4102444800,
                        "deprecated": bool(meta.get("deprecated")),
                        "popular": name in TARGETS,
                        "malicious": v in adv,
                        "advisory_id": "|".join(aliases) if v in adv else "",
                        "is_typosquat": False,
                        "maintainers": mnt,
                    },
                }
            )
            pkg_versions.setdefault(name, {})[v] = ver_id(name, v)

    planets: set[tuple[str, str]] = set()
    for repo in repos:
        full = repo["full_name"]
        lock_id = fetch_real.stable_id("Lockfile", full)
        svc_id = fetch_real.stable_id("Service", full)
        nodes.append(
            {
                "label": "Package",
                "id": fetch_real.stable_id("Package", full),
                "properties": {"name": full, "popular": False},
            }
        )
        nodes.append(
            {
                "label": "Lockfile",
                "id": lock_id,
                "properties": {
                    "name": full,
                    "app": full,
                    "service": full,
                    "created_at": repo["updated_epoch"],
                    "resolved_at": fetched_at,
                },
            }
        )
        nodes.append(
            {"label": "Service", "id": svc_id, "properties": {"name": full, "icon": ""}}
        )
        edges["USES_LOCKFILE"].append(
            {
                "edge_id": fetch_real.stable_id("USES_LOCKFILE", full),
                "source": svc_id,
                "target": lock_id,
                "properties": {
                    "since": fetched_at,
                    "valid_from": fetched_at,
                    "valid_until": 4102444800,
                },
            }
        )
        resolved: set[int] = set()
        for name, rng in repo_deps[full].items():
            pool = pkg_versions.get(name, {})
            if not pool:
                continue
            best = fetch_real.highest_satisfying(list(pool), rng)
            if best not in pool:
                continue
            nid = pool[best]
            if nid in resolved:
                continue
            resolved.add(nid)
            edges["RESOLVES_TO"].append(
                {
                    "edge_id": fetch_real.stable_id(
                        "RESOLVES_TO", f"{full}:{name}@{best}"
                    ),
                    "source": lock_id,
                    "target": nid,
                    "properties": {
                        "at": fetched_at,
                        "was_resolved_while_live": True,
                        "valid_from": fetched_at,
                        "valid_until": 4102444800,
                    },
                }
            )
            # real transitive DEPENDS_ON edges within the universe (registry metadata)
            meta = docs.get(name, {}).get("versions", {}).get(best) or {}
            for dep, drng in (meta.get("dependencies") or {}).items():
                dep_pool = pkg_versions.get(dep, {})
                dbest = (
                    fetch_real.highest_satisfying(list(dep_pool), drng)
                    if dep_pool
                    else None
                )
                if dbest and dbest in dep_pool:
                    key = (nid, dep_pool[dbest])
                    if key not in planets:
                        planets.add(key)
                        edges["DEPENDS_ON"].append(
                            {
                                "edge_id": fetch_real.stable_id(
                                    "DEPENDS_ON", f"{name}@{best}->{dep}@{dbest}"
                                ),
                                "source": nid,
                                "target": dep_pool[dbest],
                                "properties": {
                                    "range": drng,
                                    "pinned": False,
                                    "valid_from": fetch_real._iso_to_epoch(
                                        times.get(best)
                                    )
                                    or 0,
                                    "valid_until": 4102444800,
                                },
                            }
                        )

    # Package (name) + maintainer nodes
    for name in sorted(pkg_versions):
        nodes.append(
            {
                "label": "Package",
                "id": fetch_real.stable_id("Package", name),
                "properties": {"name": name, "popular": name in TARGETS},
            }
        )
    dev_ids: dict[str, int] = {}
    for n in list(nodes):
        for m in n["properties"].get("maintainers", []) or []:
            if m not in dev_ids:
                dev_ids[m] = fetch_real.stable_id("Developer", m)
                nodes.append(
                    {
                        "label": "Developer",
                        "id": dev_ids[m],
                        "properties": {"handle": m, "email": ""},
                    }
                )
    for n in nodes:
        if n["label"] != "PackageVersion":
            continue
        for m in n["properties"].get("maintainers", []) or []:
            edges["MAINTAINED_BY"].append(
                {
                    "edge_id": fetch_real.stable_id("MAINTAINED_BY", f"{n['id']}:{m}"),
                    "source": n["id"],
                    "target": dev_ids[m],
                    "properties": {
                        "since": n["properties"]["published_at"],
                        "valid_from": n["properties"]["published_at"],
                        "valid_until": 4102444800,
                    },
                }
            )

    # schema-completeness tidy + drop transient maintainers prop
    for n in nodes:
        n["properties"].pop("maintainers", None)
        for k in (
            "published_at",
            "valid_until",
            "created_at",
            "resolved_at",
            "since",
            "at",
        ):
            if n["properties"].get(k) is None:
                n["properties"][k] = 0
        if n["label"] == "Package":
            n["properties"].setdefault("popular", False)
        if n["label"] == "Developer":
            n["properties"].setdefault("email", "")
    for es in edges.values():
        for e in es:
            for k in ("valid_from", "valid_until", "since", "at"):
                if e["properties"].get(k) is None:
                    e["properties"][k] = 0

    dataset = {"nodes": nodes, "edges": edges}
    dataset_file = GITHUB / "dataset.json"
    dataset_md5 = hashlib.md5(json.dumps(dataset).encode()).hexdigest()
    dataset_file.write_text(json.dumps(dataset))

    (GITHUB / "manifest.json").write_text(
        json.dumps(
            {
                "fetched_at": fetched_at,
                "llm_curated": args.with_llm,
                "repos": [r["full_name"] for r in repos],
                "universe_packages": len(pkg_versions),
                "package_versions": sum(len(v) for v in pkg_versions.values()),
                "nodes": len(nodes),
                "edges": {k: len(v) for k, v in edges.items()},
                "vulnerable_versions": sum(len(v) for v in vuln_versions.values()),
                "dataset_md5": dataset_md5,
                "elapsed_s": round(time.time() - start, 1),
            },
            indent=1,
        )
    )

    write_ground_truth(nodes, edges, pkg_versions, osv)

    print(f"done in {time.time() - start:.1f}s")
    print(
        f"repos={len(repos)} packages={len(pkg_versions)} versions={sum(len(v) for v in pkg_versions.values())}"
        f" vulnerable={sum(len(v) for v in vuln_versions.values())} md5={dataset_md5[:10]}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""refresh_ground_truth.py — regenerate data/github/ground_truth.json over the FULL committed graph.

The committed graph is now the union of the real GitHub corpus (data/github/dataset.json)
plus every committed project snapshot (data/projects/*/snapshot.json). Ground truth is
honest by construction here exactly as in fetch_github.write_ground_truth: a version is
`malicious` iff upstream OSV says so, and `exposed_services` lists EVERY service whose
lockfile resolves it (blast radius closed over the merged DEPENDS_ON edges).

Re-running this just recomputes truth from committed data — no network, deterministic.
Run after adding a new project snapshot, then re-run pytest/eval and recommit.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from scripts.fetch_github import write_ground_truth

GITHUB = ROOT / "data" / "github"
PROJECTS = ROOT / "data" / "projects"


def merged_graph() -> tuple[list[dict], dict[str, list[dict]]]:
    """Union of corpus dataset + every committed project snapshot (deduped by node id)."""
    datasets = [json.loads((GITHUB / "dataset.json").read_text())]

    def load(path: Path) -> dict:
        return json.loads(path.read_text())

    for snap in sorted(PROJECTS.glob("*/snapshot.json")):
        datasets.append(load(snap))

    by_id: dict[int, dict] = {}
    merged_edges: dict[str, dict[tuple[int, int], dict]] = {}
    for ds in datasets:
        for n in ds["nodes"]:
            if n["label"] == "Lockfile" and "name" not in n.get("properties", {}):
                n["properties"]["name"] = n["properties"][
                    "app"
                ]  # project snapshots name services by repo ref
            by_id.setdefault(n["id"], n)
        for etype, edges in ds.get("edges", {}).items():
            bucket = merged_edges.setdefault(etype, {})
            for e in edges:
                bucket.setdefault((e["source"], e["target"]), e)
    nodes = [by_id[k] for k in sorted(by_id)]
    edges = {etype: list(bucket.values()) for etype, bucket in merged_edges.items()}
    return nodes, edges


def merged_osv() -> dict[str, list[dict]]:
    out: dict[str, dict[str, dict]] = {}

    def slurp(path: Path) -> None:
        if not path.exists():
            return
        for rec in json.loads(path.read_text()):
            name = rec.get("package")
            for vuln in rec.get("vulns", []):
                out.setdefault(name, {}).setdefault(vuln.get("id", ""), vuln)

    slurp(GITHUB / "osv" / "advisories.json")
    for cache in sorted(PROJECTS.glob("*/osv/advisories.json")):
        slurp(cache)
    return {name: list(vulns.values()) for name, vulns in sorted(out.items())}


def pkg_versions(nodes: list[dict]) -> dict[str, dict[str, int]]:
    pv: dict[str, dict[str, int]] = {}
    for n in nodes:
        if n["label"] != "PackageVersion":
            continue
        p = n["properties"]
        pv.setdefault(p["name"], {}).setdefault(p["version"], n["id"])
    return pv


def main() -> None:
    nodes, edges = merged_graph()
    write_ground_truth(nodes, edges, pkg_versions(nodes), merged_osv())
    gt = json.loads((GITHUB / "ground_truth.json").read_text())
    with_exposure = [a for a in gt["advisories"] if a.get("exposed_services")]
    n_services = len({s for a in with_exposure for s in a["exposed_services"]})
    print(
        f"rewrote data/github/ground_truth.json: {len(gt['advisories'])} advisories, "
        f"{len(with_exposure)} with live exposure, {n_services} distinct exposed services"
    )


if __name__ == "__main__":
    main()

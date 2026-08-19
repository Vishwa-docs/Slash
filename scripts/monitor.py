#!/usr/bin/env python3
"""Slash monitor — watch your dependencies for lookalikes, deprecation, and malice.

Reads watchlist.toml, and for every entry: scans the graph for near-name
typosquat candidates and checks whether the watch package's own latest version
went malicious or deprecated. Read-only; never touches HydraDB writes.

Usage:
  python scripts/monitor.py                          # check watchlist.toml
  python scripts/monitor.py --watchlist my-watch.toml --out violations.json
"""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.graph_service import run_package_lookup, run_typosquat_candidates
from src.hydradb_client import HydraDBClient


def load_watchlist(path: Path) -> list[dict]:
    with path.open("rb") as fh:
        doc = tomllib.load(fh)
    watches = doc.get("watch", [])
    if not isinstance(watches, list) or not watches:
        raise SystemExit(f"watchlist {path} has no [[watch]] entries")
    return [{"name": w["name"], "min_score": float(w.get("min_score", 0.75))} for w in watches if w.get("name")]


def monitor(client: HydraDBClient, watches: list[dict]) -> dict:
    violations: list[dict] = []
    for w in watches:
        name = w["name"]
        tp = run_typosquat_candidates(client, seed_names=[name], top_k=25)
        lookalikes = [
            {
                "watch": name,
                "kind": "typosquat",
                "name": c["name"],
                "score": c["typosquat_score"],
                "nearest_seed": c["nearest_seed"],
                "in_degree": c["in_degree"],
                "deprecated": c["deprecated"],
            }
            for c in tp["candidates"]
            if c["name"].lower() != name.lower() and c["typosquat_score"] >= w["min_score"]
        ]
        violations.extend(lookalikes)
        own = run_package_lookup(client, name, None)  # latest version
        node = own.get("node") or {}
        if node.get("malicious"):
            violations.append(
                {
                    "watch": name,
                    "kind": "own_latest_malicious",
                    "name": name,
                    "version": node.get("version"),
                    "advisory_id": node.get("advisory_id"),
                }
            )
        elif node.get("deprecated"):
            violations.append(
                {
                    "watch": name,
                    "kind": "own_latest_deprecated",
                    "name": name,
                    "version": node.get("version"),
                }
            )
    return {"watches": [w["name"] for w in watches], "violations": violations}


def render_digest(report: dict) -> str:
    lines = [f"slash monitor: {len(report['watches'])} watch(es), {len(report['violations'])} violation(s)"]
    for v in report["violations"]:
        if v["kind"] == "typosquat":
            lines.append(
                f"  ! {v['kind']}: {v['name']} (score {v['score']}) looks like "
                f"{v['nearest_seed']} — protects watch '{v['watch']}'"
            )
        else:
            lines.append(f"  ! {v['kind']}: {v['name']}@{v['version']} — watch '{v['watch']}'")
    if not report["violations"]:
        lines.append("  clean: no lookalikes or own-version degradation on watched packages")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Slash dependency watchlist monitor")
    ap.add_argument("--watchlist", default=str(ROOT / "watchlist.toml"))
    ap.add_argument("--out", help="write violations json to path")
    args = ap.parse_args()

    client = HydraDBClient()
    report = monitor(client, load_watchlist(Path(args.watchlist)))
    print(render_digest(report))
    if args.out:
        Path(args.out).write_text(json.dumps(report, indent=2))
        print(f"violations -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
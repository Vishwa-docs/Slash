#!/usr/bin/env python3
"""Diff two Snapshot manifests into a "what changed in your supply chain" digest.

This is the monitoring/retention loop: run `scripts/snapshot.py` on a cadence,
then `scripts/delta.py` to see what entered, left, or turned malicious in your
dependency tree since the last baseline.

Usage:
  python scripts/delta.py --older .hydradb/snapshots/week-01.json --newer .hydradb/snapshots/week-02.json
  python scripts/delta.py --older ... --newer ... --out digest.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def diff(o: dict, n: dict) -> dict:
    def _pairs(recs: list, key) -> set:
        return {(r[key], r.get("version")) for r in recs}

    def _keys(recs: list, key) -> set:
        return {r[key] for r in recs}

    new_packages = sorted(set(n["package_names"]) - set(o["package_names"]))
    gone_packages = sorted(set(o["package_names"]) - set(n["package_names"]))
    new_malicious = sorted(
        _pairs(n["malicious"], "name") - _pairs(o["malicious"], "name"),
        key=lambda kv: (kv[0], kv[1]),
    )
    gone_malicious = sorted(
        _pairs(o["malicious"], "name") - _pairs(n["malicious"], "name"),
        key=lambda kv: (kv[0], kv[1]),
    )
    new_typosq = sorted(_keys(n["typosquat_names"], "") - _keys(o["typosquat_names"], ""))
    gone_typosq = sorted(_keys(o["typosquat_names"], "") - _keys(n["typosquat_names"], ""))
    new_deprecated = sorted(
        _pairs(n["deprecated_versions"], "name") - _pairs(o["deprecated_versions"], "name"),
        key=lambda kv: (kv[0], kv[1]),
    )
    new_apps = sorted(set(n["lockfile_apps"]) - set(o["lockfile_apps"]))
    return {
        "older": {"label": o["label"], "snapshot_at": o["snapshot_at"]},
        "newer": {"label": n["label"], "snapshot_at": n["snapshot_at"]},
        "summary": {
            "packages": {
                "added": len(new_packages),
                "removed": len(gone_packages),
                "now": len(n["package_names"]),
            },
            "malicious": {"added": len(new_malicious), "removed": len(gone_malicious), "now": len(n["malicious"])},
            "typosquat_names": {"added": len(new_typosq), "removed": len(gone_typosq), "now": len(n["typosquat_names"])},
            "deprecated": {"added": len(new_deprecated), "now": len(n["deprecated_versions"])},
            "appearances": {"apps": {"added": new_apps, "now": n["lockfile_apps"]}},
        },
        "new_packages": new_packages,
        "gone_packages": gone_packages,
        "new_malicious": [{"name": k[0], "version": k[1]} for k in new_malicious],
        "gone_malicious": [{"name": k[0], "version": k[1]} for k in gone_malicious],
        "new_typosquat_names": new_typosq,
        "gone_typosquat_names": gone_typosq,
        "new_deprecated": [{"name": k[0], "version": k[1]} for k in new_deprecated],
    }


def render_digest(d: dict) -> str:
    s = d["summary"]
    lines = [
        f"supply-chain delta: {d['older']['label']} -> {d['newer']['label']} ({d['newer']['snapshot_at']})",
        f"  packages: +{s['packages']['added']} / -{s['packages']['removed']}  (now {s['packages']['now']})",
        f"  malicious versions: +{s['malicious']['added']} / -{s['malicious']['removed']}  (now {s['malicious']['now']})",
        f"  typosquat names: +{s['typosquat_names']['added']} / -{s['typosquat_names']['removed']}  (now {s['typosquat_names']['now']})",
        f"  deprecated versions: +{s['deprecated']['added']}  (now {s['deprecated']['now']})",
    ]
    if d["new_malicious"]:
        lines.append("  NEW MALICIOUS:")
        lines += [f"    ! {m['name']}@{m['version']}" for m in d["new_malicious"]]
    if d["new_typosquat_names"]:
        lines.append("  NEW TYPOSQUAT NAMES: " + ", ".join(d["new_typosquat_names"]))
    if s["appearances"]["apps"]["added"]:
        lines.append("  NEW APPS IN SCOPE: " + ", ".join(s["appearances"]["apps"]["added"]))
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Diff two Slash snapshots")
    ap.add_argument("--older", required=True, help="baseline snapshot json")
    ap.add_argument("--newer", required=True, help="current snapshot json")
    ap.add_argument("--out", help="write digest json to path")
    args = ap.parse_args()

    older = json.loads(Path(args.older).read_text())
    newer = json.loads(Path(args.newer).read_text())
    digest = diff(older, newer)
    print(render_digest(digest))
    if args.out:
        Path(args.out).write_text(json.dumps(digest, indent=2))
        print(f"digest -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""Snapshot the corpus so you can diff your supply chain across time.

A snapshot is a deterministic digest of the committed dataset: package names,
versions, malicious/typosquat/deprecated state, lockfile apps, and edge counts.
It is pure (no HydraDB required) and reproducible from the dataset file.

Usage:
  python scripts/snapshot.py                      # -> .hydradb/snapshots/<ts>.json
  python scripts/snapshot.py --name week-01       # -> .hydradb/snapshots/week-01.json
  python scripts/snapshot.py --corpus real
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

SNAP_DIR = ROOT / ".hydradb" / "snapshots"


def snapshot_manifest(corpus: str, label: str | None = None) -> dict:
    import datetime

    dataset_path = ROOT / "data" / corpus / "dataset.json"
    if not dataset_path.exists():
        raise SystemExit(f"no dataset at {dataset_path} (run scripts/ingest.py {corpus} first?)")
    nodes = json.loads(dataset_path.read_text()).get("nodes", [])
    edges = json.loads(dataset_path.read_text()).get("edges", {})
    versions_by_name: dict[str, list[str]] = {}
    malicious: list[dict] = []
    typosquat_names: list[str] = []
    deprecated_versions: list[dict] = []
    lockfile_apps: list[str] = []
    for n in nodes:
        p = n.get("properties", {})
        if n["label"] == "PackageVersion":
            versions_by_name.setdefault(p.get("name"), []).append(p.get("version"))
            if p.get("malicious"):
                malicious.append(
                    {"name": p["name"], "version": p["version"], "advisory_id": p.get("advisory_id")}
                )
            if p.get("is_typosquat"):
                typosquat_names.append(p.get("name"))
            if p.get("deprecated"):
                deprecated_versions.append({"name": p["name"], "version": p["version"]})
        elif n["label"] == "Lockfile" and p.get("app"):
            lockfile_apps.append(p["app"])
    return {
        "label": label or datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%MZ"),
        "snapshot_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "corpus": corpus,
        "stats": {
            "nodes": len(nodes),
            "packages": sum(1 for n in nodes if n["label"] == "Package"),
            "package_versions": len(versions_by_name),
            "malicious": len(malicious),
            "typosquat_names": len(set(typosquat_names)),
            "deprecated_versions": len(deprecated_versions),
            "lockfile_apps": len(lockfile_apps),
            "edges": {k: len(v) for k, v in edges.items()},
        },
        "package_names": sorted(versions_by_name),
        "malicious": sorted(malicious, key=lambda m: (m["name"], m["version"])),
        "typosquat_names": sorted(set(typosquat_names)),
        "deprecated_versions": sorted(deprecated_versions, key=lambda m: (m["name"], m["version"])),
        "lockfile_apps": sorted(lockfile_apps),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Snapshot the Slash corpus for time-diff reports")
    ap.add_argument("--corpus", default="generated", help="generated | real")
    ap.add_argument("--name", help="snapshot label (default: timestamp)")
    args = ap.parse_args()

    SNAP_DIR.mkdir(parents=True, exist_ok=True)
    snap = snapshot_manifest(args.corpus, args.name)
    path = SNAP_DIR / f"{snap['label']}.json"
    path.write_text(json.dumps(snap, indent=2))
    print(f"snapshot -> {path}")
    print(f"  {snap['stats']['packages']} packages, {snap['stats']['package_versions']} versions, "
          f"{snap['stats']['malicious']} malicious, {snap['stats']['typosquat_names']} typosquat names")
    return 0


if __name__ == "__main__":
    sys.exit(main())
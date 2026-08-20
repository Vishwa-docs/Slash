#!/usr/bin/env python3
"""Generate scan fixtures from the REAL GitHub corpus (no fabricated records).

Reads data/github/dataset.json + ground_truth.json and writes a tiny
package-lock.json per demo service. Each fixture pins a real package at a real
version that the corpus flags as vulnerable, so `scripts/scan.py` demonstrates
real findings against real data.

Usage: python scripts/gen_scan_fixtures.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DATASET = ROOT / "data" / "github" / "dataset.json"
GROUND_TRUTH = ROOT / "data" / "github" / "ground_truth.json"
OUT = ROOT / "data" / "scan-fixtures"


def lockfile_for(app: str, pins: dict[str, str]) -> dict:
    dependencies = {
        name: {
            "version": ver,
            "resolved": f"https://registry.npmjs.org/{name}/-/{name.split('/')[-1]}-{ver}.tgz",
        }
        for name, ver in sorted(pins.items())
    }
    return {
        "name": app,
        "version": "1.0.0",
        "lockfileVersion": 2,
        "requires": True,
        "packages": {},
        "dependencies": dependencies,
    }


def main() -> int:
    if not DATASET.exists() or not GROUND_TRUTH.exists():
        print("data/github corpus missing — run scripts/fetch_github.py first")
        return 1
    dataset = json.loads(DATASET.read_text())
    gt = json.loads(GROUND_TRUTH.read_text())

    # map (package, version) -> malicious flag from the snapshot nodes
    flagged = {
        (n["properties"]["name"], n["properties"]["version"]): n["properties"].get(
            "malicious"
        )
        for n in dataset["nodes"]
        if n.get("label") == "PackageVersion"
    }

    exposed = [a for a in gt["advisories"] if a.get("exposed_services")]
    if not exposed:
        print("no exposed advisories to pin — nothing to demonstrate")
        return 1

    adv = exposed[0]
    pins = {adv["name"]: adv["version"]}
    # add a clean dep so the fixture is a believable lockfile
    clean_deps = [
        n["properties"]["name"]
        for n in dataset["nodes"]
        if n.get("label") == "PackageVersion"
        and n["properties"]["name"] != adv["name"]
        and not flagged.get((n["properties"]["name"], n["properties"]["version"]))
    ]
    if clean_deps:
        name = clean_deps[0]
        ver = next(
            n["properties"]["version"]
            for n in dataset["nodes"]
            if n.get("label") == "PackageVersion" and n["properties"]["name"] == name
        )
        pins[name] = ver

    fixtures = {
        "checkout-svc": pins,
        # second fixture uses the next exposed advisory when available
        "merchant-api": (
            {exposed[1]["name"]: exposed[1]["version"], **pins}
            if len(exposed) > 1
            else pins
        ),
    }

    OUT.mkdir(parents=True, exist_ok=True)
    for app, app_pins in fixtures.items():
        path = OUT / app / "package-lock.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(lockfile_for(app, app_pins), indent=2))
        print(f"wrote {path} ({len(app_pins)} pins, one vulnerable)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

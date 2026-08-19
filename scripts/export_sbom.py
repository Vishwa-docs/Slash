#!/usr/bin/env python3
"""Export a CycloneDX SBOM for an app in the graph.

Usage:
  python scripts/export_sbom.py --app gateway-us              # print to stdout
  python scripts/export_sbom.py --app gateway-us --out sbom.json

The SBOM lists every package the app's lockfile resolves, tagged with any
malicious/advisory state known to the graph — a procurement-ready artifact
generated from live data, no SaaS account required.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.hydradb_client import HydraDBClient
from src.sbom import sbom_for


def main() -> int:
    ap = argparse.ArgumentParser(description="Export CycloneDX SBOM from the Slash graph")
    ap.add_argument("--app", required=True, help="app name (Lockfile.app)")
    ap.add_argument("--out", help="write SBOM to path (default stdout)")
    args = ap.parse_args()

    client = HydraDBClient()
    result = sbom_for(client, args.app)
    if not result["found"]:
        print(f"no lockfile for app '{args.app}' in graph", file=sys.stderr)
        return 1
    payload = result["sbom"]
    text = json.dumps(payload, indent=2)
    if args.out:
        Path(args.out).write_text(text)
        print(f"sbom ({result['components']} components, services: {', '.join(result['services'])}) -> {args.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
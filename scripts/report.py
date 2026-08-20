#!/usr/bin/env python3
"""Slash report — the one-page listing of everything bad in the graph right now.

Runs the batch exposure check across every advisory in the corpus: which
services are exposed, which apps resolved the bad version while it was live,
and whether the live-flag recomputation agreed.

Usage:
  python scripts/report.py
  python scripts/report.py --out report.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.hydradb_client import HydraDBClient
from src.report import exposure_report


def main() -> int:
    ap = argparse.ArgumentParser(description="Slash exposure report")
    ap.add_argument("--out", help="write report json to path")
    args = ap.parse_args()

    client = HydraDBClient()
    report = exposure_report(client)
    t = report["totals"]
    print(
        f"exposure report: {report['advisories_checked']} advisories checked, "
        f"{report['advisories_present']} present in graph"
    )
    print(
        f"  services exposed: {t['services_exposed']} · apps at risk: {t['apps_at_risk']} · "
        f"live resolutions: {t['live_resolutions']}"
    )
    if report["advisories_present"]:
        for r in report["exposures"]:
            print(
                f"  {r['advisory_id']}: {r['name']}@{r['version']} -> "
                f"{', '.join(r['services']) or 'none'} "
                f"({r['lockfile_count']} live resolution(s), recompute_agrees={r['recompute_agrees']})"
            )
    if args.out:
        Path(args.out).write_text(json.dumps(report, indent=2))
        print(f"report -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

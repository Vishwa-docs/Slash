"""Batch exposure report — the one-page view of everything bad in the graph right now.

Iterates every advisory known to the corpus and asks the graph: which services
are exposed, how many apps resolved the bad version while it was live, and did
the live-flag recomputation agree. This is the dashboard a CISO opens first.
"""

from __future__ import annotations

import time

from src.examples import overview
from src.graph_service import run_resolved_while_live
from src.hydradb_client import HydraDBClient


def _advisory_id(version: str) -> str:
    parts = version.split("-")
    if len(parts) >= 3 and parts[0] == "adv":
        return f"ADV-{parts[1]}-{parts[2]}"
    return version


def exposure_report(client: HydraDBClient) -> dict:
    t0 = time.time()
    rows = []
    for adv in overview()["exposures"]:
        r = run_resolved_while_live(client, adv["name"], adv["version"])
        if not r.get("found"):
            continue
        rows.append(
            {
                "advisory_id": _advisory_id(adv["version"]),
                "name": adv["name"],
                "version": adv["version"],
                "services": r.get("services", []),
                "lockfile_count": len(r.get("lockfiles", [])),
                "appearing": sorted({lf["app"] for lf in r.get("lockfiles", [])}),
                "resolved_while_live": [
                    {
                        "app": lf["app"],
                        "service": lf["service"],
                        "name": lf["version_name"],
                        "version": lf["version"],
                        "resolved_at": lf["resolved_at"],
                    }
                    for lf in r.get("lockfiles", [])
                ],
                "recompute_agrees": r.get("recompute_agrees"),
                "query_count": r.get("query_count", 0),
            }
        )
    return {
        "generated_ms": round((time.time() - t0) * 1000, 1),
        "advisories_checked": len(overview()["exposures"]),
        "advisories_present": len(rows),
        "exposures": rows,
        "totals": {
            "services_exposed": len({s for r in rows for s in r["services"]}),
            "apps_at_risk": len({a for r in rows for a in r["appearing"]}),
            "live_resolutions": sum(r["lockfile_count"] for r in rows),
        },
    }
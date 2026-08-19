#!/usr/bin/env python3
"""Slash scan — point Slash at a repo and get a supply-chain report.

Reads `package-lock.json` files under a directory, cross-checks every pinned
name@version against the graph, and reports: malicious versions currently
resolved, the services they expose (resolved-while-live), deprecated pins, and
typosquat lookalikes around your dependency names.

Read-only. Never writes to HydraDB (the store is schema-immutable at runtime and
writes are empty-store-only). Pins that don't exist in the corpus are reported
honestly as "unknown to corpus" rather than guessed.

Usage:
  python scripts/scan.py                # scans ./data/scan-fixtures
  python scripts/scan.py --dir ./my-app --out report.json
  python scripts/scan.py --dir ./my-app --html report.html
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.graph_service import run_resolved_while_live, run_typosquat_candidates
from src.hydradb_client import HydraDBClient

FLAG_HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Slash scan report</title>
<style>
body{font-family:"Berkeley Mono",ui-monospace,Menlo,monospace;background:#fdfcfc;color:#201d1d;margin:0;padding:32px;max-width:920px}
h1{font-size:22px;margin:0 0 4px} h2{font-size:15px;margin:28px 0 8px;border-bottom:1px solid #e3dfdb;padding-bottom:6px}
.meta{color:#6b6664;font-size:12px} .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin:16px 0}
.stat{border:1px solid #e3dfdb;border-radius:4px;padding:10px 12px} .stat .k{color:#6b6664;font-size:10px;text-transform:uppercase}
.stat .v{font-size:20px;font-weight:600;margin-top:2px} .v.danger{color:#ff3b30} .v.ok{color:#1d7a2e} .v.warn{color:#b06f00}
.app{border:1px solid #e3dfdb;border-radius:4px;padding:14px 16px;margin:12px 0;background:#fff}
.app h3{margin:0 0 6px;font-size:14px} .find{border-top:1px solid #e3dfdb;padding:8px 0;font-size:13px;display:flex;gap:8px;align-items:baseline}
.badge{display:inline-block;font-size:9.5px;letter-spacing:.05em;font-weight:700;border-radius:2px;padding:2px 6px;color:#fff}
.b--danger{background:#ff3b30} .b--warn{background:#ff9f0a;color:#3a2a00} .b--ok{background:#30d158;color:#06380f}
.b--muted{background:#8a8380} code{background:#f5f2ef;border:1px solid #e3dfdb;border-radius:3px;padding:1px 5px;font-size:12px}
.pin{display:flex;gap:8px;align-items:center;flex-wrap:wrap;border-top:1px solid #f5f2ef;padding:6px 0;font-size:12.5px}
footer{margin-top:28px;color:#6b6664;font-size:11px;border-top:1px solid #e3dfdb;padding-top:10px}
</style></head><body>
<h1>slash scan</h1><div class="meta">__META__</div>
__BODY__
<footer>Slash &mdash; deterministic supply chain blast radius on HydraDB. Every finding above came from the graph;
pins marked "unknown to corpus" mean this version is not in the scanned corpus, not that it is safe.</footer>
</body></html>"""


# --- lockfile discovery + parsing ------------------------------------------------


def find_lockfiles(directory: Path) -> list[Path]:
    if directory.is_file() and directory.name == "package-lock.json":
        return [directory]
    return sorted(p for p in directory.rglob("package-lock.json") if "node_modules" not in p.parts)


def parse_package_lock(path: Path) -> tuple[str, dict[str, str]]:
    doc = json.loads(path.read_text())
    pins: dict[str, str] = {}
    pkg_map = doc.get("packages") or {}
    node_name = doc.get("name") or path.parent.name
    if pkg_map:
        for spec, meta in pkg_map.items():
            if not spec or not isinstance(meta, dict) or not meta.get("version"):
                continue
            name = spec.split("node_modules/")[-1]
            pins[name] = meta["version"]
    else:
        for name, meta in (doc.get("dependencies") or {}).items():
            if isinstance(meta, dict) and meta.get("version"):
                pins[name] = meta["version"]
    return node_name, pins


# --- corpus manifest --------------------------------------------------------------


def corpus_manifest() -> dict:
    nodes = json.loads((ROOT / "data" / "generated" / "dataset.json").read_text()).get("nodes", [])
    versions_by_name: dict[str, set[str]] = {}
    malicious: dict[tuple, dict] = {}
    typosquat_names: set[str] = set()
    deprecated_versions: set[tuple] = set()
    for n in nodes:
        p = n.get("properties", {})
        if n["label"] == "PackageVersion":
            versions_by_name.setdefault(p.get("name"), set()).add(p.get("version"))
            if p.get("malicious"):
                malicious[(p["name"], p["version"])] = {
                    "advisory_id": p.get("advisory_id"),
                    "published_at": p.get("published_at"),
                }
            if p.get("is_typosquat"):
                typosquat_names.add(p.get("name"))
            if p.get("deprecated"):
                deprecated_versions.add((p.get("name"), p.get("version")))
    popular = {n["properties"]["name"] for n in nodes if n["label"] == "Package" and n["properties"].get("popular")}
    return {
        "versions_by_name": versions_by_name,
        "malicious": malicious,
        "typosquat_names": typosquat_names,
        "deprecated_versions": deprecated_versions,
        "popular": popular,
    }


# --- classification ---------------------------------------------------------------


def classify_pins(pins: dict[str, str], manifest: dict) -> list[dict]:
    result = []
    for name, version in pins.items():
        known = name in manifest["versions_by_name"]
        known_ver = known and version in manifest["versions_by_name"][name]
        result.append(
            {
                "name": name,
                "version": version,
                "in_corpus": known_ver,
                "new_version_of_known": known and not known_ver,
                "unknown": not known,
                "malicious": (name, version) in manifest["malicious"],
                "advisory_id": manifest["malicious"].get((name, version), {}).get("advisory_id"),
                "deprecated": (name, version) in manifest["deprecated_versions"],
                "typosquat_self": name in manifest["typosquat_names"],
                "popular": name in manifest["popular"],
            }
        )
    return result


# --- report ------------------------------------------------------------------------


def check_typosquats(client: HydraDBClient, pins: dict[str, str]) -> list[dict]:
    seeds = sorted(pins)
    res = run_typosquat_candidates(client, seed_names=seeds, top_k=25)
    banned = {s.lower() for s in seeds}
    flagged = [
        {
            "name": c["name"],
            "score": c["typosquat_score"],
            "nearest_seed": c["nearest_seed"],
            "in_degree": c["in_degree"],
            "deprecated": c["deprecated"],
        }
        for c in res["candidates"]
        if c["name"].lower() not in banned and c["typosquat_score"] >= 0.75
    ]
    return flagged


def scan_dir(client: HydraDBClient, directory: Path, only: str | None = None) -> dict:
    manifest = corpus_manifest()
    apps = []
    for path in find_lockfiles(directory):
        app, pins = parse_package_lock(path)
        if only and app != only:
            continue
        classified = classify_pins(pins, manifest)
        exposures = []
        if {"*": None} and client.healthz():
            for pin in classified:
                if not pin["malicious"]:
                    continue
                r = run_resolved_while_live(client, pin["name"], pin["version"])
                exposures.append(
                    {
                        "name": pin["name"],
                        "version": pin["version"],
                        "advisory_id": pin["advisory_id"],
                        "services": r.get("services", []),
                        "lockfiles": [
                            {
                                "service": lf["service"],
                                "app": lf["app"],
                                "resolved_at": lf["resolved_at"],
                                "was_resolved_while_live": lf["was_resolved_while_live"],
                            }
                            for lf in r.get("lockfiles", [])
                        ],
                        "recompute_agrees": r.get("recompute_agrees"),
                    }
                )
        typosquats = check_typosquats(client, pins)
        apps.append(
            {
                "app": app,
                "lockfile": str(path),
                "pins": classified,
                "exposures": exposures,
                "typosquat_flag": typosquats,
                "deprecated_pins": [p["name"] for p in classified if p["deprecated"]],
            }
        )
    total_pins = sum(len(a["pins"]) for a in apps)
    return {
        "generated_at": None,
        "apps": apps,
        "totals": {
            "apps": len(apps),
            "pins": total_pins,
            "in_corpus": sum(1 for a in apps for p in a["pins"] if p["in_corpus"]),
            "unknown": sum(1 for a in apps for p in a["pins"] if p["unknown"]),
            "malicious_resolved": sum(1 for a in apps for p in a["pins"] if p["malicious"]),
            "deprecated": sum(1 for a in apps for p in a["pins"] if p["deprecated"]),
            "typosquat_flag": sum(len(a["typosquat_flag"]) for a in apps),
        },
    }


# --- HTML render -------------------------------------------------------------------


def render_html(report: dict) -> str:
    t = report["totals"]
    stat = (
        lambda k, v, cls: f'<div class="stat"><div class="k">{k}</div>'
        f'<div class="v {cls}">{v}</div></div>'
    )
    grid = (
        '<div class="grid">'
        + stat("apps", t["apps"], "")
        + stat("pins", t["pins"], "")
        + stat("in corpus", t["in_corpus"], "ok")
        + stat("unknown to corpus", t["unknown"], "warn")
        + stat("malicious resolved", t["malicious_resolved"], "danger")
        + stat("typosquat flag", t["typosquat_flag"], "danger")
        + "</div>"
    )
    app_html = []
    for a in report["apps"]:
        rows = []
        for p in a["pins"]:
            badge = '<span class="badge b--muted">unknown</span>'
            if p["in_corpus"]:
                badge = '<span class="badge b--ok">in corpus</span>'
                if p["malicious"]:
                    badge = f'<span class="badge b--danger">malicious {p["advisory_id"]}</span>'
                elif p["deprecated"]:
                    badge = '<span class="badge b--warn">deprecated</span>'
                elif p["typosquat_self"]:
                    badge = '<span class="badge b--warn">known typosquat</span>'
            rows.append(f'<div class="pin">{badge} <code>{p["name"]}@{p["version"]}</code></div>')
        for e in a["exposures"]:
            rows.append(
                f'<div class="find"><span class="badge b--danger">exposed</span>'
                f'<div>{e["advisory_id"]}: <code>{e["name"]}@{e["version"]}</code> reaches '
                f'{" ".join(e["services"]) or "no services"} '
                f'via {len(e["lockfiles"])} lockfile resolution(s)</div></div>'
            )
        for tq in a["typosquat_flag"]:
            rows.append(
                f'<div class="find"><span class="badge b--danger">typosquat</span>'
                f'<div><code>{tq["name"]}</code> (score {tq["score"]}) looks like '
                f'<code>{tq["nearest_seed"]}</code> — {tq["in_degree"]} dependants, '
                f'{"deprecated" if tq["deprecated"] else "recent"}.</div></div>'
            )
        if not rows:
            rows = ['<div class="find"><span class="badge b--ok">clean</span><div>no findings</div></div>']
        app_html.append(
            f'<div class="app"><h3>{a["app"]}</h3><div class="meta">{a["lockfile"]}</div>'
            + "".join(rows)
            + "</div>"
        )
    return FLAG_HTML.replace("__META__", "read-only scan · import your lockfiles, we map your blast radius").replace(
        "__BODY__", grid + "".join(app_html)
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Slash supply-chain scanner")
    ap.add_argument("--dir", default=str(ROOT / "data" / "scan-fixtures"), help="directory or package-lock.json")
    ap.add_argument("--out", help="write JSON report to path")
    ap.add_argument("--html", help="write shareable HTML report to path")
    args = ap.parse_args()

    client = HydraDBClient()
    report = scan_dir(client, Path(args.dir))
    report["generated_at"] = None
    t = report["totals"]
    print(f"slash scan: {t['apps']} app(s), {t['pins']} pins "
          f"({t['in_corpus']} in corpus, {t['unknown']} unknown), "
          f"{t['malicious_resolved']} malicious resolved, {t['typosquat_flag']} typosquat flag(s)")
    if args.out:
        import datetime

        report["generated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
        Path(args.out).write_text(json.dumps(report, indent=2))
        print(f"json report -> {args.out}")
    if args.html:
        Path(args.html).write_text(render_html(report))
        print(f"html report -> {args.html}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
"""Demo material + overview stats for the Slash console (real data only).

Everything is read from the committed real-GitHub corpus snapshot
(``data/github``, built by ``scripts/fetch_github.py``): real repos, real
packages, real published versions and real OSV/CVE advisories. The console
renders instantly from this snapshot — no traversal required to draw the dashboard.

If the corpus has not been built yet (no ``data/github/manifest.json``), every
accessor returns empty/neutral values so the UI degrades gracefully instead of
crashing.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATASET = ROOT / "data" / "github" / "dataset.json"
GROUND_TRUTH = ROOT / "data" / "github" / "ground_truth.json"
MANIFEST = ROOT / "data" / "github" / "manifest.json"


def _load(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception:  # noqa: BLE001 - a partial/corrupt snapshot must not crash the UI
        return {}


def _dataset_versions() -> set[tuple[str, str]]:
    """Return set of (name, version) tuples that exist in the dataset."""
    ds = _load(DATASET)
    return {
        (n["properties"]["name"], n["properties"]["version"])
        for n in ds.get("nodes", [])
        if n.get("label") == "PackageVersion"
        and n.get("properties", {}).get("name")
        and n.get("properties", {}).get("version")
    }


def demo_examples() -> list[dict]:
    """Chips anchored to what actually exists in the real corpus.

    Advisory-driven questions are generated from the ground truth the same run
    produced, so the chips and the graph always agree. Only advisories whose
    (name, version) exist in the committed dataset are surfaced — this prevents
    chips that always fail with "not found".
    """
    gt = _load(GROUND_TRUTH)
    advisories = gt.get("advisories", [])
    ds_versions = _dataset_versions()
    # lead with advisories that actually have live exposures in the corpus,
    # most-consequential first (largest exposed-service fan-out), but only
    # if the package version actually exists in the ingested dataset
    ordered = sorted(
        (
            a
            for a in advisories
            if a.get("exposed_services")
            and (a.get("name"), a.get("version")) in ds_versions
        ),
        key=lambda a: (-len(a.get("exposed_services", [])), a.get("advisory_id", "")),
    )
    examples: list[dict] = []
    for adv in ordered[:3]:
        name, ver = adv.get("name"), adv.get("version")
        alias = (adv.get("advisory_id") or "").split("|")[0]
        if not name or not ver:
            continue
        if adv.get("exposed_services"):
            examples.append(
                {
                    "question": f"Which services are exposed by {name}@{ver}?",
                    "hint": f"advisory {alias or 'OSV'} in the corpus exposure",
                    "tag": "exposed",
                }
            )
        else:
            examples.append(
                {
                    "question": f"Which repos are exposed by {name}@{ver}?",
                    "hint": f"advisory {alias or 'OSV'} in the corpus exposure",
                    "tag": "exposed",
                }
            )
        examples.append(
            {
                "question": f"Which repos resolved {name}@{ver} while it was live?",
                "hint": "lockfile resolution history for the advisory",
                "tag": "resolved",
            }
        )
    examples += [
        {
            "question": "Is there a typosquat near axios?",
            "hint": "edit-distance lookalikes over npm package names",
            "tag": "typosquat",
        },
        {
            "question": "What is the latest version of express?",
            "hint": "package lookup against the registry metadata",
            "tag": "lookup",
        },
        {
            "question": "What is the blast radius of debug@4.4.3?",
            "hint": "transitive dependants — the core graph question",
            "tag": "blast",
        },
    ]
    return examples


def overview() -> dict:
    nodes = _load(DATASET).get("nodes", [])
    manifest = _load(MANIFEST)
    counts: dict[str, int] = {}
    for n in nodes:
        counts[n["label"]] = counts.get(n["label"], 0) + 1
    malicious = sum(1 for n in nodes if n.get("properties", {}).get("malicious"))
    adv_total = 0
    exposures: list[dict] = []
    for a in _load(GROUND_TRUTH).get("advisories", []):
        adv_total += 1
        exposures.append(
            {
                "name": a.get("name"),
                "version": a.get("version"),
                "advisory_id": a.get("advisory_id", ""),
                "services": a.get("exposed_services", []),
                # Keep the API shape aligned with the React Overview type.
                "resolved_live": a.get("resolved_live", []),
            }
        )
    return {
        "dataset": "global corpus (GitHub repos + npm + OSV)",
        "repos": manifest.get("repos", []),
        "fetched_at": manifest.get("fetched_at"),
        "dataset_md5": manifest.get("dataset_md5", ""),
        "nodes": counts,
        "total_nodes": len(nodes),
        "malicious_versions": malicious,
        "typosquat_versions": sum(
            1 for n in nodes if n.get("properties", {}).get("is_typosquat")
        ),
        "advisories": adv_total,
        "exposures": exposures,
        "examples": demo_examples(),
    }

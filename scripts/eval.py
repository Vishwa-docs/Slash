"""Phase 6 eval harness — same code paths as the app, no ground-truth visibility inside.

Holds out a subset of advisories as "recent" (simulating the track's held-out rule),
runs the live pipeline, and computes precision / recall / F1 on exposed-service sets,
p95 latency, queries-per-question, and token cost (LLM off => 0).

Usage: python scripts/eval.py  (HydraDB must be up + ingested)
Output: prints a table and rewrites docs/research/scoring.md with real numbers.
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.graph_service import (
    run_exposed_services,
    run_resolved_while_live,
)
from src.hydradb_client import HydraDBClient


def hold_out(advisories: list[dict], n: int = 2) -> list[dict]:
    """Simulate recent advisories: hold out the n latest by published_at."""
    return sorted(advisories, key=lambda a: a["published_at"])[-n:]


def score(predicted: set[str], truth: set[str]) -> dict:
    inter = predicted & truth
    p = len(inter) / len(predicted) if predicted else 0.0
    r = len(inter) / len(truth) if truth else 0.0
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    return {"precision": p, "recall": r, "f1": f1}


def main() -> int:
    gt = json.loads((ROOT / "data" / "generated" / "ground_truth.json").read_text())
    client = HydraDBClient()

    recent = hold_out(gt["advisories"])
    rows: list[dict] = []
    all_latency: list[float] = []
    total_queries = 0

    for adv in recent:
        start = time.perf_counter()
        res = run_exposed_services(client, adv["name"], adv["version"])
        wall = (time.perf_counter() - start) * 1000
        all_latency.append(wall)
        total_queries += res["query_count"]

        predicted = set(res["services"])
        truth = set(adv["exposed_services"])
        s = score(predicted, truth)
        wl = run_resolved_while_live(client, adv["name"], adv["version"])
        wl_truth = {
            f"{l['app']}::{l['service']}" for l in adv["resolved_while_live_lockfiles"]
        }
        wl_pred = {f"{l['app']}::{l['service']}" for l in wl["lockfiles"]}
        wl_s = score(wl_pred, wl_truth)
        rows.append(
            {
                "advisory": adv["advisory_id"],
                "query_precision": f"{s['precision']:.2f}",
                "query_recall": f"{s['recall']:.2f}",
                "query_f1": f"{s['f1']:.2f}",
                "resolved_while_live_f1": f"{wl_s['f1']:.2f}",
                "recompute_agrees": str(wl.get("recompute_agrees", True)).lower(),
                "latency_ms": f"{wall:.0f}",
                "queries": res["query_count"],
            }
        )

    header = [
        "advisory",
        "query_precision",
        "query_recall",
        "query_f1",
        "resolved_while_live_f1",
        "recompute_agrees",
        "latency_ms",
        "queries",
    ]
    sep = "| " + " | ".join("---" for _ in header) + " |"
    out = ["| " + " | ".join(header) + " |", sep]
    for r in rows:
        out.append("| " + " | ".join(str(r[h]) for h in header) + " |")

    p95 = f"{statistics.quantiles(all_latency, n=20)[18]:.0f}" if all_latency else "n/a"
    mean_prec = statistics.mean(float(r["query_precision"]) for r in rows)
    mean_rec = statistics.mean(float(r["query_recall"]) for r in rows)
    mean_f1 = statistics.mean(float(r["query_f1"]) for r in rows)
    summary = {
        "advisories_evaluated": len(rows),
        "precision_mean": f"{mean_prec:.2f}",
        "recall_mean": f"{mean_rec:.2f}",
        "f1_mean": f"{mean_f1:.2f}",
        "latency_p95_ms": p95,
        "queries_total": total_queries,
        "queries_per_question": f"{total_queries / len(rows):.1f}" if rows else "n/a",
        "token_cost": 0,  # LLM off — deterministic Researcher + Adjudicator
    }

    table = "\n".join(out)
    print(table)
    print("\nSummary:", json.dumps(summary, indent=2))

    scoring = ROOT / "docs" / "research" / "scoring.md"
    scoring.write_text(
        f"""# Scoring Methodology & Results

> Source of truth: `changes/CHG-0001/test-plan/` + these live numbers from `.evidence/runs/phase-6/eval.txt`.

## Ground truth
`data/generated/ground_truth.json` records, per advisory:
- the malicious `PackageVersion` (`name`, `version`, window),
- the true exposed service set (transitive reverse-dependency closure within our 6-hop ceiling),
- the true "resolved-while-live" lockfile set,
- the planted typosquats.

## Metrics
| Metric | Definition | Target |
|---|---|---|
| Precision | | predicted exposed ∩ true exposed | / | predicted exposed | | report |
| Recall | | predicted exposed ∩ true exposed | / | true exposed | | report |
| F1 | harmonic mean | report |
| Query latency p95 | wall-clock per question-phrase (client `elapsed_ms`) | < 1 s |
| Cost | queries-per-question and (if LLM on) tokens | cap + report |

## Procedure
1. Hold out a subset of advisories as "recent" (simulating the track's held-out rule).
2. Run Slash **without** ground truth visibility.
3. Compute metrics; render table into README + this file.

## Results (auto-generated {time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())})
Held-out advisories: {", ".join(r["advisory"] for r in rows)} ({len(rows)} latest by published_at).

{table}

### Summary
- Mean precision {summary["precision_mean"]} · mean recall {summary["recall_mean"]} · mean F1 {summary["f1_mean"]}
- p95 per-question latency {summary["latency_p95_ms"]} ms (budget < 1 s)
- {summary["queries_total"]} queries across {len(rows)} questions ({summary["queries_per_question"]} / question)
- Token cost: {summary["token_cost"]} (deterministic pipeline — no LLM in the loop)

Raw run: `.evidence/runs/phase-6/eval.txt`.
"""
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

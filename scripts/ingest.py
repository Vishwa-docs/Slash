#!/usr/bin/env python3
"""Idempotent UNWIND batch ingest of a dataset.json into HydraDB.

Node upserts use `MERGE ... SET` by integer id; edge upserts use
`MERGE ... [r:TYPE {id: row.edge_id}]` so re-running never duplicates.
Real data only: the same supply-chain schema covers both real corpora.
Usage: python scripts/ingest.py [--dataset github|real]   (default: github)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.hydradb_client import HydraDBClient
from src.schema import EDGE_PROPS, NODE_PROPS

BATCH = 500

LENS_PROP_SETS: dict[str, tuple[dict, dict]] = {
    "github": (NODE_PROPS, EDGE_PROPS),
    "real": (NODE_PROPS, EDGE_PROPS),
}


def batches(rows: list) -> list[list]:
    return [rows[i : i + BATCH] for i in range(0, len(rows), BATCH)]


def upsert_nodes(client: HydraDBClient, dataset: dict, node_props: dict) -> None:
    by_label: dict[str, list] = {}
    for node in dataset["nodes"]:
        by_label.setdefault(node["label"], []).append(node)
    for label, props in node_props.items():
        rows = by_label.get(label, [])
        if not rows:
            continue
        set_clause = ", ".join(f"n.{k} = row.{k}" for k in props)
        for chunk in batches(rows):
            params = [{"id": n["id"], **n["properties"]} for n in chunk]
            client.query(
                f"UNWIND $rows AS row MERGE (n {{id: row.id}}) SET n:{label}, {set_clause}",
                {"rows": params},
            )
        print(f"nodes {label}: {len(rows)}")


def upsert_edges(client: HydraDBClient, dataset: dict, edge_props: dict) -> None:
    for etype, (src_label, dst_label, props) in edge_props.items():
        rows = dataset["edges"].get(etype, [])
        if not rows:
            continue
        set_clause = ", ".join(f"r.{k} = row.{k}" for k in props)
        for chunk in batches(rows):
            params = [
                {
                    "source": e["source"],
                    "target": e["target"],
                    "edge_id": e["edge_id"],
                    **e["properties"],
                }
                for e in chunk
            ]
            client.query(
                f"UNWIND $rows AS row MATCH (s:{src_label} {{id: row.source}}), (d:{dst_label} {{id: row.target}}) "
                f"MERGE (s)-[r:{etype} {{id: row.edge_id}}]->(d) SET {set_clause}",
                {"rows": params},
            )
        print(f"edges {etype}: {len(rows)}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--dataset",
        choices=["github", "real"],
        default="github",
        help="dataset directory under data/ (both are real corpora; github = GitHub-repo corpus)",
    )
    args = ap.parse_args()
    which = args.dataset
    if which not in LENS_PROP_SETS:
        print(f"Skipping {which}: no schema property set registered.")
        return
    node_props, edge_props = LENS_PROP_SETS[which]
    path = ROOT / "data" / which / "dataset.json"
    dataset = json.loads(path.read_text())
    client = HydraDBClient()
    upsert_nodes(client, dataset, node_props)
    upsert_edges(client, dataset, edge_props)


if __name__ == "__main__":
    main()

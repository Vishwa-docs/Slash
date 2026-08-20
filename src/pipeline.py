"""Question pipeline: classify -> execute -> audit -> adjudicate, with a healer.

Works for any active lens (dependency graph by default; fraud swaps the
vocabulary and the graph schema it queries). The core Resolver → Auditor →
Adjudicator path is grounded in the graph — the graph is the ground truth.

Optional LLM refinement (ADR-0011): when the caller supplies an API key (or
``GROQ_API_KEY`` is set) and opts in, the plan entities are normalized and a
short executive summary is attached to the verdict. Both steps are best-effort
and fall back to the base result on any failure — running without a key
produces the same answers.

Self-heal on a gap: instead of flat abstention, the Healer first tries to
materialize the missing facts (from the committed corpus snapshot, then a
live npm registry + OSV lookup) and re-runs the query. Only if the graph still
cannot answer is the verdict marked ``reported=True`` and the gap written to
``data/report/support-requests.json``.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import hashlib
import json
import time

import fetch_real

import src.graph_service as gs
from src import adjudicate, intent
from src import llm as llm_mod
from src.hydradb_client import HydraDBClient
from src.lens import SUPPLY_CHAIN, Lens
from src.models import IntentClass, QueryPlan, Verdict
from src.schema import NODE_PROPS

ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = ROOT / "data" / "report"
SNAPSHOT = ROOT / "data" / "github" / "dataset.json"
POPULAR_TARGETS = {
    "ws",
    "axios",
    "minimist",
    "express",
    "lodash",
    "jsonwebtoken",
    "marked",
    "fastify",
}


def _load_snapshot() -> dict:
    if not SNAPSHOT.exists():
        return {}
    try:
        return json.loads(SNAPSHOT.read_text())
    except Exception:  # noqa: BLE001
        return {}


def _record_unresolved(question: str, reason: str) -> None:
    """Persist a question the graph (even after healing) could not answer."""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORT_DIR / "support-requests.json"
    rows: list[dict] = []
    if path.exists():
        try:
            rows = json.loads(path.read_text())
        except Exception:  # noqa: BLE001
            rows = []
    rows.append({"ts": int(time.time()), "question": question, "reason": reason})
    path.write_text(json.dumps(rows, indent=1))


def _upsert_nodes(client: HydraDBClient, label: str, rows: list[dict]) -> bool:
    props = NODE_PROPS.get(label, [])
    if not rows or not props:
        return False
    set_clause = ", ".join(f"n.{k} = row.{k}" for k in props)
    try:
        client.query(
            f"UNWIND $rows AS row MERGE (n {{id: row.id}}) SET n:{label}, {set_clause}",
            {"rows": rows},
        )
        return True
    except Exception:  # noqa: BLE001 - a read-only store rejects the heal; report the gap
        return False


def _heal(client: HydraDBClient, plan: QueryPlan) -> bool:
    """Try to materialize the missing package data, then signal retry.

    Order: committed real snapshot first (no network), then live npm + OSV.
    Returns True when the plan's package now has at least one version in the
    live graph, so the caller can re-run the query.
    """
    name = plan.package or ""
    if not name:
        return False

    snapshot = _load_snapshot()
    if snapshot:
        ver_rows = [
            {"id": n["id"], **n["properties"]}
            for n in snapshot.get("nodes", [])
            if n.get("label") == "PackageVersion"
            and n.get("properties", {}).get("name") == name
        ]
        if ver_rows and _upsert_nodes(client, "PackageVersion", ver_rows):
            pkg_id = next(
                (
                    n["id"]
                    for n in snapshot.get("nodes", [])
                    if n.get("label") == "Package"
                    and n.get("properties", {}).get("name") == name
                ),
                None,
            )
            if pkg_id is not None:
                _upsert_nodes(
                    client,
                    "Package",
                    [{"id": pkg_id, "name": name, "popular": name in POPULAR_TARGETS}],
                )
            return True

    # registry heal: pull real metadata and insert the requested/its latest version
    doc = fetch_real.fetch_npm_docs([name]).get(name, {})
    if not doc or not doc.get("versions"):
        return False
    version = (
        plan.version
        or fetch_real.highest_satisfying(list(doc["versions"]), "latest")
        or max(doc["versions"])
    )
    meta = doc.get("versions", {}).get(version)
    if not meta:
        return False
    times = doc.get("time", {})

    def sid(key: str) -> int:
        return int(hashlib.sha256(key.encode()).hexdigest()[:15], 16)

    propset = {
        "id": sid(f"PackageVersion:{name}@{version}"),
        "name": name,
        "version": version,
        "published_at": fetch_real._iso_to_epoch(times.get(version)) or 0,
        "valid_until": 4102444800,
        "deprecated": bool(meta.get("deprecated")),
        "popular": False,
        "malicious": False,
        "advisory_id": "",
        "is_typosquat": False,
    }
    if _upsert_nodes(client, "PackageVersion", [propset]):
        return _upsert_nodes(
            client,
            "Package",
            [{"id": sid(f"Package:{name}"), "name": name, "popular": False}],
        )
    return False


def resolve_version(
    client: HydraDBClient, plan: QueryPlan, lens: Lens = SUPPLY_CHAIN
) -> QueryPlan:
    """Fill a missing version with the latest published version of the package."""
    if plan.version or not plan.package:
        return plan
    r = gs.execute(client, [gs.plan_latest_version(plan.package, lens)])[0].result
    if r.rows:
        return plan.model_copy(update={"version": r.rows[0]["version"]})
    return plan


def _paper_plan(question: str, plan: QueryPlan, key: str | None = None) -> QueryPlan:
    """Apply LLM-normalized entities back onto the base plan.

    Intent is only overridden when the base parser abstained
    (UNSUPPORTED) — the graph query engine never trusts a model for ground truth.
    """
    refined = llm_mod.refine_plan(question, plan.model_dump(), key=key)
    updates: dict = {}
    for k in ("package", "version", "developer"):
        val = refined.get(k)
        if isinstance(val, str) and val.strip():
            updates[k] = val.strip()
    seeds = refined.get("seed_names")
    if isinstance(seeds, list):
        names = [s.strip() for s in seeds if isinstance(s, str) and s.strip()]
        if names:
            updates["seed_names"] = names
    if plan.intent == IntentClass.UNSUPPORTED:
        intent_name = refined.get("intent")
        if isinstance(intent_name, str) and intent_name.upper() in {
            m.name for m in IntentClass
        }:
            updates["intent"] = IntentClass(intent_name.upper())
    if not updates:
        return plan
    return plan.model_copy(update=updates)


def answer(client: HydraDBClient, question: str, lens: Lens = SUPPLY_CHAIN) -> Verdict:
    verdict, _ = answer_with_result(client, question, lens)
    return verdict


def answer_with_result(
    client: HydraDBClient,
    question: str,
    lens: Lens = SUPPLY_CHAIN,
    llm: bool = False,
    llm_key: str | None = None,
) -> tuple[Verdict, dict | None]:
    plan = intent.classify(question)
    if llm and llm_mod.available(llm_key):
        plan = _paper_plan(question, plan, key=llm_key)
    if plan.intent == IntentClass.UNSUPPORTED:
        verdict = adjudicate.Adjudicator().verdict(adjudicate.Audit(plan=plan), lens)
        verdict.reported = True
        _record_unresolved(question, verdict.reason)
        if llm and llm_mod.available(llm_key):
            verdict.summary = llm_mod.summarize(
                question, verdict.model_dump(), lens.id, key=llm_key
            )
        return verdict, None
    plan = resolve_version(client, plan, lens)

    runner = {
        IntentClass.BLAST_RADIUS: lambda p: gs.run_blast_radius(
            client, p.package, p.version or "", lens=lens
        ),
        IntentClass.EXPOSED_SERVICES: lambda p: gs.run_exposed_services(
            client, p.package, p.version or "", lens=lens
        ),
        IntentClass.RESOLVED_WHILE_LIVE: lambda p: gs.run_resolved_while_live(
            client, p.package, p.version or "", lens=lens
        ),
        IntentClass.MAINTAINER_CONTAGION: lambda p: gs.run_maintainer_contagion(
            client, p.developer or "", lens=lens
        ),
        IntentClass.TYPOSQUAT_CANDIDATES: lambda p: gs.run_typosquat_candidates(
            client, p.seed_names or None, lens=lens
        ),
        IntentClass.PACKAGE_LOOKUP: lambda p: gs.run_package_lookup(
            client, p.package or "", p.version, lens=lens
        ),
    }[plan.intent]

    result = runner(plan)
    audit = adjudicate.Auditor().evaluate(plan, result)
    verdict = adjudicate.Adjudicator().verdict(audit, lens)
    if verdict.abstain:
        healed = _heal(client, plan)
        if healed:
            result = runner(plan)
            audit = adjudicate.Auditor().evaluate(plan, result)
            healed_verdict = adjudicate.Adjudicator().verdict(audit, lens)
            verdict = healed_verdict.model_copy(
                update={"healed": not healed_verdict.abstain}
            )
        if verdict.abstain:
            verdict = verdict.model_copy(
                update={
                    "reported": True,
                    "reason": (
                        verdict.reason
                        + " The gap was written to the support report (self-heal "
                        "could not construct it)."
                    ),
                }
            )
            _record_unresolved(question, verdict.reason)
    if llm and llm_mod.available(llm_key):
        verdict.summary = llm_mod.summarize(
            question, verdict.model_dump(), lens.id, key=llm_key
        )
    return verdict, result

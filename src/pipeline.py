"""Deterministic question pipeline: classify -> execute -> audit -> verdict.

Works for any active lens (supply-chain by default; fraud swaps the vocabulary
and the graph schema it queries). Everything is deterministic — no LLM key is
required for the product to run (ADR-0006).

Optional LLM refinement (ADR-0011): when ``llm=True`` and ``GROQ_API_KEY`` is set,
the plan entities are normalized and a short executive summary is attached to the
verdict. Both steps are best-effort and fall back to the deterministic result on
any failure — running without a key produces identical answers.
"""

from __future__ import annotations

import src.graph_service as gs
from src import adjudicate, intent, llm
from src.hydradb_client import HydraDBClient
from src.lens import Lens, SUPPLY_CHAIN
from src.models import IntentClass, QueryPlan, Verdict


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


def _paper_plan(question: str, plan: QueryPlan) -> QueryPlan:
    """Apply LLP-normalized entities back onto the deterministic plan.

    Intent is only overridden when the deterministic parser abstained
    (UNSUPPORTED) — the graph query engine never trusts a model for ground truth.
    """
    refined = llm.refine_plan(question, plan.model_dump())
    updates: dict = {}
    for key in ("package", "version", "developer"):
        val = refined.get(key)
        if isinstance(val, str) and val.strip():
            updates[key] = val.strip()
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
) -> tuple[Verdict, dict | None]:
    plan = intent.classify(question)
    if llm and llm.available():
        plan = _paper_plan(question, plan)
    if plan.intent == IntentClass.UNSUPPORTED:
        verdict = adjudicate.Adjudicator().verdict(adjudicate.Audit(plan=plan), lens)
        if llm and llm.available():
            verdict.summary = llm.summarize(question, verdict.model_dump(), lens.id)
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
    if llm and llm.available():
        verdict.summary = llm.summarize(question, verdict.model_dump(), lens.id)
    return verdict, result
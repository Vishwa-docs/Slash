"""Auditor + Adjudicator personas. Deterministic evidence checks -> Verdict.

Auditor consumes a `run_*` result dict from src.graph_service and scores
subgraph density + temporal consistency + contradictions. Adjudicator maps the
audit to a first-class Verdict (answer with evidence chain, or abstention).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.lens import SUPPLY_CHAIN, Lens
from src.models import Evidence, IntentClass, QueryPlan, Verdict

DENSITY_THRESHOLD = 0.3


@dataclass
class Audit:
    plan: QueryPlan
    result: dict = field(default_factory=dict)
    density: float = 0.0
    contradictions: list[dict] = field(default_factory=list)
    found: bool = False
    evidence: list[Evidence] = field(default_factory=list)
    latency_ms: float = 0.0
    query_count: int = 0


def _evidence_chain(result: dict) -> list[Evidence]:
    chain: list[Evidence] = []
    for step, res in result.get("steps", []):
        rows = res.result.rows if hasattr(res, "result") else res.rows
        elapsed = res.result.elapsed_ms if hasattr(res, "result") else res.elapsed_ms
        chain.append(
            Evidence(
                purpose=step.purpose,
                cypher=step.cypher,
                params=step.params,
                row_count=len(rows),
                elapsed_ms=elapsed,
            )
        )
    return chain


class Auditor:
    """Scores an already-executed graph_service result dict (never queries)."""

    def __init__(self, density_threshold: float = DENSITY_THRESHOLD) -> None:
        self.density_threshold = density_threshold

    def evaluate(self, plan: QueryPlan, result: dict) -> Audit:
        intent = plan.intent
        audit = Audit(
            plan=plan,
            result=result,
            evidence=_evidence_chain(result),
            latency_ms=result.get("elapsed_ms", 0.0),
            query_count=result.get("query_count", len(result.get("steps", []))),
        )
        if intent == IntentClass.EXPOSED_SERVICES:
            audit.found = bool(result.get("found"))
            audit.density = 1.0 if result.get("services") else 0.0
        elif intent == IntentClass.BLAST_RADIUS:
            audit.found = bool(result.get("found"))
            audit.density = 1.0 if result.get("dependant_count", 0) > 0 else 0.0
        elif intent == IntentClass.RESOLVED_WHILE_LIVE:
            audit.found = bool(result.get("found"))
            # "no lockfile resolved while live" is a valid answer, not missing evidence
            audit.density = 1.0 if audit.found else 0.0
            audit.contradictions = result.get("contradictions", [])
        elif intent == IntentClass.MAINTAINER_CONTAGION:
            audit.found = bool(result.get("found"))
            audit.density = 1.0 if audit.found else 0.0
        elif intent == IntentClass.TYPOSQUAT_CANDIDATES:
            audit.found = bool(result.get("found"))
            audit.density = 1.0 if result.get("candidates") else 0.0
        elif intent == IntentClass.PACKAGE_LOOKUP:
            audit.found = bool(result.get("found"))
            audit.density = 1.0 if audit.found else 0.0
        return audit


class Adjudicator:
    """Maps an Audit to a Verdict; abstains on unsupported / empty evidence."""

    def verdict(self, audit: Audit, lens: Lens = SUPPLY_CHAIN) -> Verdict:
        plan = audit.plan
        if plan.intent == IntentClass.UNSUPPORTED:
            return Verdict(
                intent=plan.intent,
                abstain=True,
                reason=(
                    "I can answer blast-radius, exposed-services, resolved-while-live, "
                    "maintainer-contagion, typosquat, and package-lookup questions."
                ),
                evidence_chain=[],
            )
        if not audit.found or audit.density < DENSITY_THRESHOLD:
            return Verdict(
                intent=plan.intent,
                abstain=True,
                reason="Not enough evidence in the graph for this question.",
                evidence_chain=audit.evidence,
                latency_ms=audit.latency_ms,
                query_count=audit.query_count,
            )
        answer = self._answer(plan, audit, lens)
        reason = ""
        if audit.contradictions:
            reason = (
                f"{len(audit.contradictions)} contradiction(s) detected and resolved "
                "in favor of recomputed timestamps"
            )
        return Verdict(
            intent=plan.intent,
            answer=answer,
            evidence_chain=audit.evidence,
            abstain=False,
            reason=reason,
            latency_ms=audit.latency_ms,
            query_count=audit.query_count,
        )

    def _answer(self, plan: QueryPlan, audit: Audit, lens: Lens = SUPPLY_CHAIN) -> str:
        r = audit.result
        intent = plan.intent
        if intent == IntentClass.EXPOSED_SERVICES:
            return (
                ", ".join(r.get("services", []))
                if r.get("services")
                else f"No {lens.exposed_noun} are exposed."
            )
        if intent == IntentClass.BLAST_RADIUS:
            return (
                f"Blast radius of {plan.package}@{plan.version or '?'}: "
                f"{r.get('dependant_count', 0)} {lens.dependant_noun} in <=6 hops"
            )
        if intent == IntentClass.RESOLVED_WHILE_LIVE:
            if audit.contradictions:
                both = " | ".join(
                    f"{c['name']}@{c['version']}: stored={c['stored_flag']}, recomputed={c['recomputed_flag']}"
                    for c in audit.contradictions
                )
                return f"{len(r.get('lockfiles', []))} {lens.live_noun}; contradiction: {both}"
            return f"{len(r.get('lockfiles', []))} {lens.live_noun}"
        if intent == IntentClass.MAINTAINER_CONTAGION:
            return f"{plan.developer} {lens.contagion_verb} {len(r.get('packages', []))} {lens.contagion_noun}: {', '.join(r.get('packages', []))}"
        if intent == IntentClass.TYPOSQUAT_CANDIDATES:
            top = r.get("candidates", [])[:5]
            return ", ".join(
                f"{c['name']} (score {c.get('typosquat_score', c.get('score', 0))})"
                for c in top
            )
        if intent == IntentClass.PACKAGE_LOOKUP:
            node = r.get("node") or {}
            if not node:
                return f"No {lens.version_noun} {plan.version or ''} of {plan.package} found in the graph."
            bits = [
                f"{node.get('name')}@{node.get('version')}",
                f"published {node.get('published_at')}",
            ]
            if lens.malicious_field in node:
                bits.append(f"{lens.malicious_field}={node.get(lens.malicious_field)}")
            if node.get("is_typosquat") is not None:
                bits.append(f"is_typosquat={node.get('is_typosquat')}")
            return ", ".join(bits)
        return ""

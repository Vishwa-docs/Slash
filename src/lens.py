"""Domain lenses — proof that Slash is one engine for any connected data.

A Lens parameterizes the graph layer (labels, relations, the "compromised"
property) and the answer vocabulary. The five primitives are schema-agnostic:
exposure, resolved-inside-a-suspicious-window, shared-owner contagion, name
lookalikes, and blast radius all reduce to the same queries with different
label names.

Currently shipped lenses:
  SUPPLY_CHAIN  — npm-style dependency ecosystems (flagship, hackathon track)
  FRAUD         — AML/intake graphs: compromised account states, merchants, inflows

Adding a new vertical is: define a Lens + generate a dataset + write examples.
No query engine changes.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Lens:
    id: str
    title: str
    # graph shape
    entity_node: str  # Package  -> Account
    version_node: str  # PackageVersion -> AccountState
    resource_node: str  # Service  -> Merchant
    consumption_node: str  # Lockfile -> IntakeEvent
    developer_node: str  # Developer -> Customer
    depend_rel: str  # DEPENDS_ON   -> TRANSFERS_TO
    uses_rel: str  # USES_LOCKFILE -> FEEDS_INTO
    resolves_rel: str  # RESOLVES_TO  -> INVOLVES
    maintains_rel: str  # MAINTAINED_BY -> OWNS
    malicious_field: str  # malicious   -> compromised
    # vocabulary
    version_entity_name: str  # "package"      -> "account state"
    version_noun: str  # "version"      -> "account state"
    exposed_noun: str  # "services"     -> "merchants"
    live_noun: str  # "lockfile(s) resolved while live" -> "intake event(s) inside the compromise window"
    dependant_noun: str  # "dependant version(s)"             -> "inflow state(s)"
    contagion_verb: str  # "maintains"    -> "owns"
    contagion_noun: str  # "package(s)"   -> "account(s)"
    lookalike_noun: str  # "typosquat"    -> "lookalike"
    all_resource_names: bool = (
        False  # True when there is no resource catalog query needed
    )
    control_verbs: tuple[str, ...] = field(
        default=("resolved", "lockfile", "live", "pinned")
    )


SUPPLY_CHAIN = Lens(
    id="supply-chain",
    title="Supply chain",
    entity_node="Package",
    version_node="PackageVersion",
    resource_node="Service",
    consumption_node="Lockfile",
    developer_node="Developer",
    depend_rel="DEPENDS_ON",
    uses_rel="USES_LOCKFILE",
    resolves_rel="RESOLVES_TO",
    maintains_rel="MAINTAINED_BY",
    malicious_field="malicious",
    version_entity_name="package",
    version_noun="version",
    exposed_noun="services",
    live_noun="lockfile(s) resolved while live",
    dependant_noun="dependant version(s)",
    contagion_verb="maintains",
    contagion_noun="package(s)",
    lookalike_noun="typosquat",
    control_verbs=("resolved", "lockfile", "live", "pinned"),
)

FRAUD = Lens(
    id="fraud",
    title="Fraud & AML",
    entity_node="Account",
    version_node="AccountState",
    resource_node="Merchant",
    consumption_node="IntakeEvent",
    developer_node="Customer",
    depend_rel="TRANSFERS_TO",
    uses_rel="FEEDS_INTO",
    resolves_rel="INVOLVES",
    maintains_rel="OWNS",
    malicious_field="compromised",
    version_entity_name="account state",
    version_noun="account state",
    exposed_noun="merchants",
    live_noun="intake event(s) inside the compromise window",
    dependant_noun="inflow state(s)",
    contagion_verb="owns",
    contagion_noun="account(s)",
    lookalike_noun="lookalike",
    control_verbs=("intake", "transfer", "moved", "during", "window"),
)

LENSES: dict[str, Lens] = {l.id: l for l in (SUPPLY_CHAIN, FRAUD)}


def lens_by_id(lens_id: str | None) -> Lens:
    return LENSES.get(lens_id or SUPPLY_CHAIN.id, SUPPLY_CHAIN)

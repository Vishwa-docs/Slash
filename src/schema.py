"""Slash schema constants — single source of truth for HydraDB labels/props.

HydraDB node identity is the integer `id` property; edges are matched by a
unique `edge_id` property so `MERGE` stays idempotent across re-ingests.
Temporal openness uses the sentinel ``VALID_UNTIL_LIVE`` (no `IS NULL`, ADR-0004).
"""

VALID_UNTIL_LIVE = 9999999999

# Node labels
PACKAGE = "Package"  # registry entry (name, popularity)
PACKAGE_VERSION = "PackageVersion"  # a resolvable version of a package
DEVELOPER = "Developer"
SERVICE = "Service"
LOCKFILE = "Lockfile"

# Edge types (directed; dependant -> dependency for DEPENDS_ON)
DEPENDS_ON = "DEPENDS_ON"  # PackageVersion -> PackageVersion
RESOLVES_TO = "RESOLVES_TO"  # Lockfile -> PackageVersion
USES_LOCKFILE = "USES_LOCKFILE"  # Service -> Lockfile
MAINTAINED_BY = "MAINTAINED_BY"  # PackageVersion -> Developer

# Label -> property keys written at ingest (the `id` is the MERGE identity).
NODE_PROPS = {
    PACKAGE: ("name", "popular"),
    PACKAGE_VERSION: (
        "name",
        "version",
        "published_at",
        "valid_until",
        "deprecated",
        "popular",
        "malicious",
        "advisory_id",
        "is_typosquat",
    ),
    DEVELOPER: ("handle", "email"),
    SERVICE: ("name",),
    LOCKFILE: ("app", "created_at", "resolved_at"),
}

# Edge type -> (source label, target label, property keys written at ingest).
EDGE_PROPS = {
    DEPENDS_ON: (
        PACKAGE_VERSION,
        PACKAGE_VERSION,
        ("edge_id", "pinned", "valid_from", "valid_until"),
    ),
    RESOLVES_TO: (
        LOCKFILE,
        PACKAGE_VERSION,
        ("edge_id", "at", "was_resolved_while_live", "valid_from", "valid_until"),
    ),
    USES_LOCKFILE: (
        SERVICE,
        LOCKFILE,
        ("edge_id", "since", "valid_from", "valid_until"),
    ),
    MAINTAINED_BY: (
        PACKAGE_VERSION,
        DEVELOPER,
        ("edge_id", "since", "valid_from", "valid_until"),
    ),
}

# Index hints: HydraDB derives adjacency indexes per edge type during its
# background index builds. These are the edge axes the product hotspots read on
# (ADR-0007: keep blast-radius traversals bounded and index-friendly).
INDEX_HINTS = (
    (DEPENDS_ON, PACKAGE_VERSION, PACKAGE_VERSION),
    (RESOLVES_TO, LOCKFILE, PACKAGE_VERSION),
    (USES_LOCKFILE, SERVICE, LOCKFILE),
    (MAINTAINED_BY, PACKAGE_VERSION, DEVELOPER),
)

MAX_HOPS = 6  # bounded variable-length path ceiling used across queries (ADR-0007)


# ---------------------------------------------------------------------------
# Fraud & AML lens (ADR-0010): same five primitives, different labels.
# AccountState ~ PackageVersion, Merchant ~ Service, IntakeEvent ~ Lockfile,
# Customer ~ Developer. "Compromised" is the amenability analog of "malicious".
# ---------------------------------------------------------------------------

ACCOUNT = "Account"  # registry entry (account name, popularity)
ACCOUNT_STATE = "AccountState"  # a resolvable state of an account
CUSTOMER = "Customer"
MERCHANT = "Merchant"  # payout/onboarding surface an account transacts through
INTAKE_EVENT = "IntakeEvent"  # a funds intake observation

TRANSFERS_TO = "TRANSFERS_TO"  # AccountState -> AccountState (upstream inflow)
INVOLVES = "INVOLVES"  # IntakeEvent -> AccountState
FEEDS_INTO = "FEEDS_INTO"  # Merchant -> IntakeEvent
OWNS = "OWNS"  # AccountState -> Customer

FRAUD_NODE_PROPS = {
    ACCOUNT: ("name", "popular"),
    ACCOUNT_STATE: (
        "name",
        "version",
        "published_at",
        "valid_until",
        "deprecated",
        "popular",
        "compromised",
        "advisory_id",
        "is_typosquat",
    ),
    CUSTOMER: ("handle", "email"),
    MERCHANT: ("name",),
    INTAKE_EVENT: ("app", "created_at", "resolved_at"),
}

FRAUD_EDGE_PROPS = {
    TRANSFERS_TO: (
        ACCOUNT_STATE,
        ACCOUNT_STATE,
        ("edge_id", "pinned", "valid_from", "valid_until"),
    ),
    INVOLVES: (
        INTAKE_EVENT,
        ACCOUNT_STATE,
        ("edge_id", "at", "was_resolved_while_live", "valid_from", "valid_until"),
    ),
    FEEDS_INTO: (
        MERCHANT,
        INTAKE_EVENT,
        ("edge_id", "since", "valid_from", "valid_until"),
    ),
    OWNS: (
        ACCOUNT_STATE,
        CUSTOMER,
        ("edge_id", "since", "valid_from", "valid_until"),
    ),
}

#!/usr/bin/env bash
# Slash smoke test. Two modes:
#   default      READ-only checks against a LIVE/populated DB (healthz, schema present, no-injection).
#   --write-probe CREATE -> MATCH -> no-injection -> DETACH DELETE cycle. HydraDB 500s on CREATE/DELETE
#                   once the store is populated (verified 2026-08-19, hydradb-notes.md §Phase 6), so the
#                   write-probe must run against a FRESH EMPTY store. Prints PASS/FAIL; exits non-zero on failure.
set -euo pipefail
cd "$(dirname "$0")/.."

MODE="${1:-}"
python3 - "$MODE" <<'PY'
import sys

MODE = sys.argv[1] if len(sys.argv) > 1 else ""

sys.path.insert(0, ".")
from src.hydradb_client import HydraDBClient, HydraDBError

PROBE_ID = 424242

fails = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global fails
    print(f"{'PASS' if ok else 'FAIL'}: {name}" + (f"  ({detail})" if detail and not ok else ""))
    if not ok:
        fails += 1


c = HydraDBClient()

# 1. healthz
check("healthz", c.healthz())

if sys.argv[1] != "--write-probe":
    # READ-ONLY mode against the populated store: the schema we ingest must be queryable.
    try:
        r = c.query("MATCH (n:Package) RETURN count(*) AS c")
        check("Package nodes readable", len(r.rows) == 1 and r.rows[0]["c"] > 0, f"rows={r.rows}")
    except HydraDBError as e:
        check("Package nodes readable", False, str(e))

    try:
        r = c.query("MATCH (n:PackageVersion) RETURN count(*) AS c")
        check("PackageVersion nodes readable", len(r.rows) == 1 and r.rows[0]["c"] > 0, f"rows={r.rows}")
    except HydraDBError as e:
        check("PackageVersion nodes readable", False, str(e))

    sys.exit(1 if fails else 0)

# WRITE-PROBE mode (requires a FRESH EMPTY store, see header comment).
PROBE_NAME = "probe-424242"

# 2. CREATE a labeled probe node + one edge (CREATE supports one-hop paths only)
try:
    c.query(
        "CREATE (a:Probe {id: $x, name: $pn})-[:FOLLOWS]->(b {id: $y})",
        {"x": PROBE_ID, "pn": PROBE_NAME, "y": PROBE_ID + 1},
    )
    check("CREATE probe node", True)
except HydraDBError as e:
    check("CREATE probe node", False, str(e))

# 3. MATCH it back by id
try:
    r = c.query("MATCH (n:Probe {id: $id}) RETURN n.id AS id", {"id": PROBE_ID})
    check("MATCH probe node back", len(r.rows) == 1 and r.rows[0]["id"] == PROBE_ID, f"rows={r.rows}")
except HydraDBError as e:
    check("MATCH probe node back", False, str(e))

# 4. no-injection check: injection string passed as a VALUE, must be treated as data
injection = f'{PROBE_NAME}") DETACH DELETE (x) //'
try:
    r = c.query("MATCH (n:Probe {name: $name}) RETURN count(n.id) AS c", {"name": injection})
    check("injection value treated as data (count 0)", len(r.rows) == 1 and r.rows[0]["c"] == 0, f"rows={r.rows}")
except HydraDBError as e:
    check("injection value treated as data (count 0)", False, str(e))

# 5. probe node untouched (nothing spliced or deleted by step 4)
try:
    r = c.query("MATCH (n:Probe {id: $id}) RETURN count(n.id) AS c", {"id": PROBE_ID})
    check("probe node untouched after injection query", len(r.rows) == 1 and r.rows[0]["c"] == 1, f"rows={r.rows}")
except HydraDBError as e:
    check("probe node untouched after injection query", False, str(e))

# 6. DETACH DELETE the probe node
try:
    c.query("MATCH (n:Probe {id: $id}) DETACH DELETE n", {"id": PROBE_ID})
    check("DETACH DELETE probe node", True)
except HydraDBError as e:
    check("DETACH DELETE probe node", False, str(e))

# 7. confirm it is gone
try:
    r = c.query("MATCH (n:Probe {id: $id}) RETURN count(n.id) AS c", {"id": PROBE_ID})
    check("probe node gone after delete", len(r.rows) == 1 and r.rows[0]["c"] == 0, f"rows={r.rows}")
except HydraDBError as e:
    check("probe node gone after delete", False, str(e))

sys.exit(1 if fails else 0)
PY
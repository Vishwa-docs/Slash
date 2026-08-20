"""CycloneDX SBOM export for Slash.

A Bill of Materials is the procurement/compliance artifact every SCA vendor sells
(Socket and Snyk gate it behind Business/Enterprise tiers). Ours is free,
self-hosted, and generated straight from the HydraDB graph: every component is
cross-referenced with malicious/advisory state at export time.

`build_cyclonedx` is pure and unit-testable; `sbom_for` fetches the resolutions
from the live graph.
"""

from __future__ import annotations

import json
from collections.abc import Callable

from src.hydradb_client import HydraDBClient

SERIAL = "urn:uuid:00000000-0000-0000-0000-000000000001"


def _purl(name: str, version: str) -> str:
    import urllib.parse

    safe = urllib.parse.quote(name, safe="")
    ver = urllib.parse.quote(version, safe="")
    return f"pkg:npm/{safe}@{ver}"


def build_cyclonedx(
    app: str,
    services: list[str],
    rows: list[dict],
    lens: str = "dependency-graph",
    serial: str = SERIAL,
    now: Callable[[], str] | None = None,
) -> dict:
    if now is None:
        import datetime

        now = lambda: datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    components = []
    for r in sorted(
        rows, key=lambda x: (x.get("name") or "") + (x.get("version") or "")
    ):
        name, version = r["name"], r["version"]
        props = []
        if r.get("malicious"):
            props.append({"name": "slash:malicious", "value": "true"})
        if r.get("advisory_id"):
            props.append({"name": "slash:advisory", "value": r["advisory_id"]})
        if r.get("deprecated"):
            props.append({"name": "slash:deprecated", "value": "true"})
        component = {
            "type": "library",
            "bom-ref": f"{name}@{version}",
            "name": name,
            "version": version,
            "purl": _purl(name, version),
        }
        if props:
            component["properties"] = props
        components.append(component)
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": serial,
        "version": 1,
        "metadata": {
            "timestamp": now(),
            "tools": [{"vendor": "slash", "name": "slash", "version": lens}],
            "component": {
                "type": "application",
                "bom-ref": app,
                "name": app,
                "version": lens,
            },
        },
        "components": components,
        "properties": [
            {"name": "slash:services", "value": ", ".join(services)},
            {"name": "slash:generated-from", "value": "HydraDB"},
        ],
    }


def sbom_for(client: HydraDBClient, app: str) -> dict:
    node = client.query(
        "MATCH (lf:Lockfile {app: $app})-[:RESOLVES_TO]->(v:PackageVersion) "
        "RETURN v.name AS name, v.version AS version, v.malicious AS malicious, "
        "v.deprecated AS deprecated, v.advisory_id AS advisory_id",
        {"app": app},
    )
    svc = client.query(
        "MATCH (s:Service)-[:USES_LOCKFILE]->(lf:Lockfile {app: $app}) RETURN s.name AS name",
        {"app": app},
    )
    if not node.rows and not svc.rows:
        return {"found": False, "app": app, "services": [], "components": 0}
    services = sorted({r["name"] for r in svc.rows})
    rows = [
        {
            "name": r["name"],
            "version": r["version"],
            "malicious": bool(r.get("malicious")),
            "deprecated": bool(r.get("deprecated")),
            "advisory_id": r.get("advisory_id"),
        }
        for r in node.rows
    ]
    return {
        "found": True,
        "app": app,
        "services": services,
        "components": len(rows),
        "sbom": build_cyclonedx(app, services, rows),
    }


def to_bytes(sbom: dict) -> bytes:
    return json.dumps(sbom, indent=2).encode()

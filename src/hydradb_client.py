"""HydraDB HTTPS query client. Stdlib only (urllib)."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path


class HydraDBError(RuntimeError):
    """Raised on non-2xx responses or malformed query results."""


@dataclass
class QueryResult:
    rows: list[dict]
    elapsed_ms: float
    columns: list[str] = field(default_factory=list)


class HydraDBClient:
    """Minimal client for HydraDB's HTTPS query API (127.0.0.1:8443).

    TODO(ADR-0003): Bolt 5.x path (neo4j driver on 7687) is not required yet;
    add only if a later phase needs it.
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8443",
        token_file: str = ".hydradb/auth.token",
        namespace: str = "default",
        cell_id: str = "cell-0",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        try:
            self.token = Path(token_file).read_text().strip()
        except OSError:
            # Local UI/API startup must remain usable before HydraDB is provisioned.
            self.token = ""
        self.namespace = namespace
        self.cell_id = cell_id

    def healthz(self) -> bool:
        try:
            with urllib.request.urlopen(f"{self.base_url}/healthz", timeout=3) as resp:
                return resp.status == 200
        except (urllib.error.URLError, OSError):
            return False

    def query(self, cypher: str, params: dict | None = None) -> QueryResult:
        body: dict = {
            "cell_id": self.cell_id,
            "query": cypher,
            "consistency": "causal",
        }
        if params:
            body["parameters"] = params
        req = urllib.request.Request(
            f"{self.base_url}/v1/graphs/default/query",
            data=json.dumps(body).encode(),
            headers={
                "Authorization": f"Bearer {self.token}",
                "X-Graph-Namespace": self.namespace,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        start = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            raise HydraDBError(
                f"HTTP {e.code}: {e.read().decode(errors='replace')}"
            ) from e
        except (urllib.error.URLError, OSError, json.JSONDecodeError) as e:
            raise HydraDBError(f"request failed: {e}") from e
        elapsed_ms = (time.monotonic() - start) * 1000.0

        if (
            not isinstance(payload, dict)
            or "columns" not in payload
            or "rows" not in payload
        ):
            raise HydraDBError(f"malformed response: {payload!r}")

        columns = payload["columns"]
        rows = []
        for row in payload["rows"]:
            if len(row) != len(columns):
                raise HydraDBError(f"row/column count mismatch: {row!r}")
            rows.append(
                {
                    col: cell.get("value") if isinstance(cell, dict) else cell
                    for col, cell in zip(columns, row)
                }
            )
        return QueryResult(rows=rows, elapsed_ms=elapsed_ms, columns=columns)

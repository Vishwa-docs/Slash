"""Slash product API — a small stdlib JSON HTTP server over the pipeline.

Endpoints (all JSON):
    GET  /api/health               HydraDB liveness
    GET  /api/overview             global corpus stats + curated demo examples
    GET  /api/projects             registered repositories (projects)
    POST /api/projects {url}       add a GitHub repo as a project (real graph)
    GET  /api/projects/{id}        project overview + sessions + example chips
    POST /api/projects/{id}/sessions {title}   open a chat session for a project
    POST /api/projects/{id}/ask {question, session_id, llm_key}
         run the pipeline scoped to the project; persists the turn
    POST /api/projects/{id}/scan   per-project exposure report
    POST /api/ask {question, llm_key}      global pipeline run (corpus lens)
    POST /api/subgraph {name,version}      nearby subgraph for the graph panel
    POST /api/keycheck {llm_key}   validate a Groq key via the free /models call

Static files from assets/app/dist/ are served with an SPA fallback so scripts/serve.py
can run the whole product from one process. The graph is always the ground truth;
a Groq key (per-request, never persisted) only adds a plan-normalizer + a summary.
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import projects
from src.examples import overview
from src.hydradb_client import HydraDBClient
from src.lens import SUPPLY_CHAIN, lens_by_id
from src.llm import check_key
from src.models import IntentClass
from src.pipeline import answer_with_result
from src.report import exposure_report
from src.sbom import sbom_for

DIST = ROOT / "assets" / "app" / "dist"
MIME = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript",
    ".css": "text/css",
    ".json": "application/json",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
    ".woff2": "font/woff2",
    ".map": "application/json",
}


def _safe(value: object) -> object:
    """Coerce pipeline internals into JSON-safe scalars (drop unsupported types)."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(k): _safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_safe(v) for v in value]
    return str(value)


def payload_for(intent: IntentClass, result: dict | None) -> dict:
    """Slice the runner result into a small, render-ready payload for the UI."""
    if not result:
        return {}
    if intent in (
        IntentClass.EXPOSED_SERVICES,
        IntentClass.RESOLVED_WHILE_LIVE,
        IntentClass.BLAST_RADIUS,
    ):
        node = (
            result.get("node") or (result.get("blast_radius") or {}).get("node") or {}
        )
        payload = {"found": result.get("found", False)}
        if payload["found"]:
            payload["node_id"] = node.get("id")
            payload["name"] = node.get("name")
            payload["version"] = node.get("version")
            payload["services"] = result.get("services", [])
            payload["paths"] = [
                {
                    "service": p["service"],
                    "app": p.get("app"),
                    "name": p.get("version_name"),
                    "version": p.get("version"),
                    "resolved_at": p.get("resolved_at"),
                    "flag": bool(p.get("flag")),
                }
                for p in result.get("path_rows", [])
            ]
        if intent is IntentClass.RESOLVED_WHILE_LIVE:
            payload["lockfiles"] = [
                {
                    "app": l["app"],
                    "service": l["service"],
                    "name": l["version_name"],
                    "version": l["version"],
                    "resolved_at": l["resolved_at"],
                }
                for l in result.get("lockfiles", [])
            ]
            payload["recompute_agrees"] = result.get("recompute_agrees")
            payload["contradictions"] = result.get("contradictions", [])
        if intent is IntentClass.BLAST_RADIUS:
            payload["dependant_count"] = result.get("dependant_count", 0)
            payload["levels"] = [
                [
                    {"id": n["id"], "name": n["name"], "version": n["version"]}
                    for n in level
                ]
                for level in result.get("levels", [])
            ]
        return payload
    if intent is IntentClass.MAINTAINER_CONTAGION:
        return {
            "found": result.get("found", False),
            "developer": result.get("developer"),
            "packages": result.get("packages", []),
        }
    if intent is IntentClass.TYPOSQUAT_CANDIDATES:
        return {
            "found": result.get("found", False),
            "seeds": result.get("seeds", []),
            "candidates": [
                {
                    "id": c["id"],
                    "name": c["name"],
                    "nearest_seed": c.get("nearest_seed"),
                    "score": c.get("typosquat_score", c.get("score", 0)),
                    "in_degree": c.get("in_degree", 0),
                    "deprecated": c.get("deprecated", False),
                }
                for c in result.get("candidates", [])
            ],
        }
    if intent is IntentClass.PACKAGE_LOOKUP:
        node = result.get("node") or {}
        payload = {"found": result.get("found", False)}
        if node:
            payload["node_id"] = node.get("id")
            payload["name"] = node.get("name")
            payload["version"] = node.get("version")
            payload["node"] = {
                k: node.get(k)
                for k in (
                    "name",
                    "version",
                    "published_at",
                    "deprecated",
                    "malicious",
                    "advisory_id",
                    "is_typosquat",
                )
                if k in node
            }
        return payload
    return {}


class SlashServer(ThreadingHTTPServer):
    client: HydraDBClient
    lens: object = SUPPLY_CHAIN


class Handler(BaseHTTPRequestHandler):
    server_version = "Slash/1.0"

    def log_message(self, fmt: str, *args: object) -> None:  # keep logs quiet
        return

    # -- helpers -----------------------------------------------------------
    def _send(self, code: int, body: bytes, ctype: str = "application/json") -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, payload: object) -> None:
        self._send(code, json.dumps(payload).encode())

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            return json.loads(raw or b"{}")
        except json.JSONDecodeError:
            return {}

    def _static(self, rel: str) -> None:
        if not DIST.exists():
            self._json(
                503, {"error": "frontend not built — run `npm run build` in assets/app"}
            )
            return
        path = (DIST / rel).resolve()
        try:
            path.relative_to(DIST.resolve())
        except ValueError:
            self._json(403, {"error": "forbidden"})
            return
        if not path.exists():
            if (
                rel.startswith("api/")
                or rel.endswith("/")
                or "." not in rel.split("/")[-1]
            ):
                path = DIST / "index.html"  # SPA fallback
            else:
                self._json(404, {"error": "not found"})
                return
        body = path.read_bytes()
        self._send(200, body, MIME.get(path.suffix, "application/octet-stream"))

    # -- routing -----------------------------------------------------------
    def do_GET(self) -> None:
        url = urllib.parse.urlparse(self.path)
        if url.path == "/api/health":
            return self._health()
        if url.path == "/api/overview":
            return self._json(200, overview())
        if url.path == "/api/report":
            return self._report()
        if url.path == "/api/projects":
            return self._json(200, {"projects": projects.list_projects()})
        m = re.fullmatch(r"/api/projects/([A-Za-z0-9._-]+)", url.path)
        if m:
            return self._json(200, projects.overview(m.group(1)))
        if url.path.startswith("/api/"):
            return self._json(404, {"error": "no such endpoint"})
        return self._static(url.path.lstrip("/") or "index.html")

    def do_POST(self) -> None:
        url = urllib.parse.urlparse(self.path)
        body = self._body()
        if url.path == "/api/ask":
            return self._ask(
                body.get("question", ""),
                body.get("lens"),
                bool(body.get("llm")),
                body.get("llm_key"),
            )
        if url.path == "/api/subgraph":
            return self._subgraph(
                body.get("name", ""), body.get("version", ""), body.get("lens")
            )
        if url.path == "/api/sbom":
            return self._sbom(body.get("app", ""))
        if url.path == "/api/projects":
            return self._add_project(body.get("url", ""))
        if url.path == "/api/keycheck":
            return self._json(200, {"ok": check_key(body.get("llm_key"))})
        m = re.fullmatch(r"/api/projects/([A-Za-z0-9._-]+)/([a-z]+)", url.path)
        if m:
            pid, action = m.group(1), m.group(2)
            if action == "sessions":
                return self._json(
                    200,
                    projects.new_session(pid, body.get("title"))
                    or {"error": "project not found"},
                )
            if action == "ask":
                return self._json(
                    200,
                    projects.ask(
                        pid,
                        body.get("question", ""),
                        body.get("session_id"),
                        body.get("llm_key"),
                    ),
                )
            if action == "scan":
                return self._json(200, projects.scan(pid))
        return self._json(404, {"error": "no such endpoint"})

    # -- handlers ----------------------------------------------------------
    def _health(self) -> None:
        try:
            ok = self.server.client.healthz()
        except Exception as e:  # noqa: BLE001
            self._json(200, {"ok": False, "hydradb": str(e)})
            return
        self._json(200, {"ok": ok, "hydradb": "connected" if ok else "down"})

    def _report(self) -> None:
        try:
            self._json(200, exposure_report(self.server.client))
        except Exception as e:  # noqa: BLE001
            self._json(503, {"error": f"report failed: {e}"})

    def _ask(
        self,
        question: str,
        lens_id: str | None = None,
        llm: bool = False,
        llm_key: str | None = None,
    ) -> None:
        if not question or not question.strip():
            return self._json(400, {"error": "question is required"})
        lens = lens_by_id(lens_id)
        t0 = time.time()
        try:
            verdict, result = answer_with_result(
                self.server.client, question, lens, llm=llm, llm_key=llm_key
            )
        except Exception as e:  # noqa: BLE001
            return self._json(503, {"error": f"pipeline failed: {e}"})
        payload = payload_for(verdict.intent, result)
        self._json(
            200,
            {
                "question": question,
                "intent": verdict.intent.value,
                "answer": verdict.answer,
                "summary": verdict.summary,
                "abstain": verdict.abstain,
                "reported": verdict.reported,
                "reason": verdict.reason,
                "latency_ms": round(verdict.latency_ms, 2),
                "query_count": verdict.query_count,
                "evidence_chain": [
                    {
                        "purpose": e.purpose,
                        "cypher": e.cypher,
                        "params": e.params,
                        "row_count": e.row_count,
                        "elapsed_ms": round(e.elapsed_ms, 2),
                    }
                    for e in verdict.evidence_chain
                ],
                "payload": payload,
                "server_ms": round((time.time() - t0) * 1000, 2),
            },
        )

    def _subgraph(self, name: str, version: str, lens_id: str | None = None) -> None:
        from src import graph_service as gs

        if not name:
            return self._json(400, {"error": "name is required"})
        lens = lens_by_id(lens_id)
        _, _, node = gs._lookup(self.server.client, name, version, lens)
        if node is None:
            return self._json(
                404, {"found": False, "error": f"{name}@{version} not in graph"}
            )
        sub = gs.run_fetch_subgraph(
            self.server.client, int(node["id"]), depth=2, lens=lens
        )
        self._json(
            200,
            {
                "node_id": sub["node_id"],
                "nodes": [
                    {
                        "id": n["id"],
                        "name": n.get("name"),
                        "version": n.get("version"),
                        "via": n.get("via"),
                    }
                    for n in sub["nodes"]
                ],
                "edges": sub["edges"],
                "elapsed_ms": round(sub["elapsed_ms"], 2),
            },
        )

    def _sbom(self, app: str) -> None:
        if not app:
            return self._json(400, {"error": "app is required"})
        try:
            result = sbom_for(self.server.client, app)
        except Exception as e:  # noqa: BLE001
            return self._json(503, {"error": f"sbom failed: {e}"})
        if not result["found"]:
            return self._json(404, {"error": f"no lockfile for app '{app}' in graph"})
        self._json(
            200,
            {
                "app": app,
                "services": result["services"],
                "components": result["components"],
                "sbom": result["sbom"],
            },
        )

    def _add_project(self, url: str) -> None:
        if not url or not url.strip():
            return self._json(
                400, {"error": "a GitHub URL (or owner/name) is required"}
            )
        try:
            record = projects.generate_project(url.strip())
        except ValueError as e:
            return self._json(400, {"error": str(e)})
        except Exception as e:  # noqa: BLE001
            return self._json(502, {"error": f"project generation failed: {e}"})
        self._json(
            200,
            {
                "id": record["id"],
                "repo": record["repo"],
                "stats": record["stats"],
            },
        )


def make_server(
    client: HydraDBClient,
    host: str = "127.0.0.1",
    port: int = 8501,
    lens: object = SUPPLY_CHAIN,
) -> SlashServer:
    projects.sync_all()
    server = SlashServer((host, port), Handler)
    server.client = client
    server.lens = lens
    return server


if __name__ == "__main__":
    client = HydraDBClient()
    server = make_server(client)
    print(
        f"Slash API + UI on http://127.0.0.1:{server.server_address[1]}  (Ctrl-C to stop)"
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()

"""Optional LLM layer for Slash — Groq, OpenAI-compatible chat, zero new deps.

Everything here is best-effort and strictly optional (ADR-0006, ADR-0011): the
graph is always the ground truth. The caller may supply a Groq API key per
request (the console sends the key the user typed; it is never persisted). When
no key is given or a call fails, every function degrades to the base graph
behaviour, so a demo run without a key produces the same answers.

Three capabilities, used only when the caller opts in:
  - ``refine_plan``   normalize entities/intent the base classifier may miss
  - ``summarize``     turn a base verdict into a 2-3 sentence executive summary
  - ``pick_repos``    suggest notable open-source GitHub repos for a target ecosystem dep
"""

from __future__ import annotations

import json
import os
import ssl
import urllib.request

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODELS_URL = "https://api.groq.com/openai/v1/models"
UA = "Mozilla/5.0 (Slash; hack-hydra-2026) urllib"


def api_key(explicit: str | None = None) -> str | None:
    if explicit and explicit.strip():
        return explicit.strip()
    return os.environ.get("GROQ_API_KEY") or None


def model_name() -> str:
    return os.environ.get("GROQ_MODEL") or "openai/gpt-oss-120b"


def available(explicit: str | None = None) -> bool:
    return api_key(explicit) is not None


def check_key(explicit: str | None = None) -> bool:
    """Validate a Groq key against the free /models endpoint (no tokens used)."""
    token = api_key(explicit)
    if not token:
        return False
    req = urllib.request.Request(
        GROQ_MODELS_URL,
        method="GET",
        headers={"Authorization": f"Bearer {token}", "User-Agent": UA},
    )
    try:
        with urllib.request.urlopen(req, timeout=10, context=_context()) as resp:
            return resp.status == 200
    except Exception:  # noqa: BLE001 - an invalid key is just an invalid key
        return False


def _context():
    """A TLS context that prefers certifi and degrades to unverified locally."""
    try:
        import certifi  # type: ignore

        return ssl.create_default_context(cafile=certifi.where())
    except (ImportError, OSError, ssl.SSLError):
        return ssl._create_unverified_context()


def chat(
    messages: list[dict],
    json_mode: bool = True,
    timeout: int = 45,
    key: str | None = None,
) -> str | None:
    """Single chat-completions round-trip; returns the assistant message text."""
    token = api_key(key)
    if not token:
        return None
    body: dict = {
        "model": model_name(),
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 700,
    }
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    req = urllib.request.Request(
        GROQ_URL,
        method="POST",
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": UA,
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_context()) as resp:
            data = json.loads(resp.read().decode())
        return data["choices"][0]["message"]["content"]
    except Exception:  # noqa: BLE001 - best-effort: fall back to the base path
        return None


def _json(text: str | None) -> dict | None:
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


INTENTS = (
    "BLAST_RADIUS",
    "EXPOSED_SERVICES",
    "RESOLVED_WHILE_LIVE",
    "MAINTAINER_CONTAGION",
    "TYPOSQUAT_CANDIDATES",
    "PACKAGE_LOOKUP",
    "UNSUPPORTED",
)


def refine_plan(question: str, current: dict, key: str | None = None) -> dict:
    """Best-effort normalization of a base QueryPlan.

    ``current`` is the plan's ``model_dump()``; we never invent names — the prompt
    forces nulls over guesses. Any failure returns ``current`` unchanged.
    """
    system = (
        "You repair a parsed question for a graph-query planner. Return ONLY JSON "
        f"with keys intent (one of {', '.join(INTENTS)}), package (string or null), "
        "version (string or null), developer (string or null), seed_names (array of "
        "strings). Use null when the question does not clearly name one. Never invent "
        "package or developer names that are not spelled in the question."
    )
    text = chat(
        [
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": json.dumps({"question": question, "plan": current}),
            },
        ],
        key=key,
    )
    parsed = _json(text)
    if parsed is None or not isinstance(parsed, dict):
        return current
    out = dict(current)
    for k in ("package", "version", "developer"):
        val = parsed.get(k)
        if isinstance(val, str) and val.strip():
            out[k] = val.strip()
    if isinstance(parsed.get("seed_names"), list):
        names = [s for s in parsed["seed_names"] if isinstance(s, str) and s.strip()]
        if names:
            out["seed_names"] = names
    intent = parsed.get("intent")
    if isinstance(intent, str) and intent.upper() in INTENTS:
        out["intent"] = intent.upper()
    return out


def summarize(question: str, verdict: dict, lens: str, key: str | None = None) -> str:
    """2-3 sentence executive summary of a verdict; '' on any failure."""
    text = chat(
        [
            {
                "role": "system",
                "content": (
                    "You are the narrator for a database hackathon demo that answers "
                    "questions over a graph. Write 2-3 crisp sentences summarizing the "
                    "verdict, quoting the concrete numbers/names already computed. "
                    "Do not add facts that are not in the verdict. Return ONLY JSON "
                    '{"summary": "..."}.'
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "lens": lens,
                        "question": question,
                        "intent": verdict.get("intent"),
                        "answer": verdict.get("answer"),
                        "abstain": verdict.get("abstain"),
                        "reason": verdict.get("reason"),
                        "query_count": verdict.get("query_count"),
                    }
                ),
            },
        ],
        key=key,
    )
    parsed = _json(text)
    if not parsed or not isinstance(parsed.get("summary"), str):
        return ""
    return parsed["summary"].strip()


def pick_repos(
    ecosystem_name: str,
    count: int = 12,
    ecosystem: str = "npm",
    key: str | None = None,
) -> list[str]:
    """Top ``count`` repo full-names the model guesses for a given ecosystem package."""
    text = chat(
        [
            {
                "role": "system",
                "content": (
                    "You curate a real-world demo corpus for a dependency-intelligence tool. "
                    f'Return ONLY JSON {{"repos": [string GitHub full-names]}} with '
                    f"{count} notable open-source JavaScript/{ecosystem} projects "
                    "that plausibly depend on the given package. Use only well-known "
                    "real repositories (e.g. vercel/next.js)."
                ),
            },
            {
                "role": "user",
                "content": ecosystem_name,
            },
        ],
        key=key,
    )
    parsed = _json(text)
    if not parsed or not isinstance(parsed.get("repos"), list):
        return []
    repos = []
    for r in parsed["repos"]:
        if isinstance(r, str) and "/" in r and len(r.split("/")) == 2:
            repos.append(r)
    return repos[:count]

"""Optional LLM layer for Slash — Groq, OpenAI-compatible chat, zero new deps.

Everything here is best-effort and strictly optional (ADR-0006, ADR-0011):
the deterministic pipeline never requires a key. When ``GROQ_API_KEY`` is unset
or a call fails, every function degrades to the deterministic behaviour, so a
video/demo run without network produces identical output to one with it.

Three capabilities, used only when the caller opts in:
  - ``refine_plan``   normalize entities/intent the deterministic classifier may miss
  - ``summarize``     turn a deterministic verdict into a 2-3 sentence executive summary
  - ``pick_repos``    suggest notable open-source GitHub repos for a target ecosystem dep
"""

from __future__ import annotations

import json
import os
import ssl
import urllib.request

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
UA = "Mozilla/5.0 (Slash; hack-hydra-2026) urllib"


def api_key() -> str | None:
    return os.environ.get("GROQ_API_KEY") or None


def model_name() -> str:
    return os.environ.get("GROQ_MODEL") or "openai/gpt-oss-120b"


def available() -> bool:
    return api_key() is not None


def chat(messages: list[dict], json_mode: bool = True, timeout: int = 45) -> str | None:
    """Single chat-completions round-trip; returns the assistant message text."""
    if not available():
        return None
    body: dict = {
        "model": model_name(),
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 700,
    }
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    ctx = None
    try:
        import certifi  # type: ignore

        ctx = ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        ctx = ssl._create_unverified_context()
    req = urllib.request.Request(
        GROQ_URL,
        method="POST",
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {api_key()}",
            "Content-Type": "application/json",
            "User-Agent": UA,
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            data = json.loads(resp.read().decode())
        return data["choices"][0]["message"]["content"]
    except Exception:  # noqa: BLE001 - best-effort: fall back to deterministic
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


def refine_plan(question: str, current: dict) -> dict:
    """Best-effort normalization of a deterministic QueryPlan.

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
            {"role": "user", "content": json.dumps({"question": question, "plan": current})},
        ]
    )
    parsed = _json(text)
    if parsed is None or not isinstance(parsed, dict):
        return current
    out = dict(current)
    for key in ("package", "version", "developer"):
        val = parsed.get(key)
        if isinstance(val, str) and val.strip():
            out[key] = val.strip()
    if isinstance(parsed.get("seed_names"), list):
        names = [s for s in parsed["seed_names"] if isinstance(s, str) and s.strip()]
        if names:
            out["seed_names"] = names
    intent = parsed.get("intent")
    if isinstance(intent, str) and intent.upper() in INTENTS:
        out["intent"] = intent.upper()
    return out


def summarize(question: str, verdict: dict, lens: str) -> str:
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
        ]
    )
    parsed = _json(text)
    if not parsed or not isinstance(parsed.get("summary"), str):
        return ""
    return parsed["summary"].strip()


def pick_repos(ecosystem_name: str, count: int = 12, ecosystem: str = "npm") -> list[str]:
    """Top ``count`` repo full-names the model guesses for a given ecosystem package."""
    text = chat(
        [
            {
                "role": "system",
                "content": (
                    "You curate a real-world demo corpus for a supply-chain tool. "
                    f"Return ONLY JSON {{\"repos\": [string GitHub full-names]}} with "
                    f"{count} notable open-source JavaScript/{ecosystem} projects "
                    "that plausibly depend on the given package. Use only well-known "
                    "real repositories (e.g. vercel/next.js)."
                ),
            },
            {
                "role": "user",
                "content": ecosystem_name,
            },
        ]
    )
    parsed = _json(text)
    if not parsed or not isinstance(parsed.get("repos"), list):
        return []
    repos = []
    for r in parsed["repos"]:
        if isinstance(r, str) and "/" in r and len(r.split("/")) == 2:
            repos.append(r)
    return repos[:count]
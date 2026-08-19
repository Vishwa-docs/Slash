"""Deterministic Researcher: question -> QueryPlan. No LLM required.

Keyword/entity patterns over normalized tokens. Optional LLM refinement is out
of scope (no key at runtime), per ADR-0006.
"""

from __future__ import annotations

import re

from src.models import IntentClass, QueryPlan

STOPWORDS = {
    "a",
    "an",
    "the",
    "of",
    "in",
    "on",
    "at",
    "for",
    "to",
    "and",
    "or",
    "is",
    "are",
    "was",
    "were",
    "what",
    "which",
    "who",
    "show",
    "tell",
    "me",
    "about",
    "does",
    "do",
    "did",
    "any",
    "all",
    "by",
    "from",
    "that",
    "with",
    "near",
    "package",
    "packages",
    "question",
    "answer",
    "compromise",
    "compromised",
    "compromises",
    "advisory",
    "attack",
    "threat",
    "malicious",
    "please",
    "name",
    "names",
    "its",
    "there",
    "has",
    "have",
    "it",
    "when",
    "involved",
    "events",
    "accounts",
    "merchants",
}

# Common English words that are never package names (helps "what is the weather"
# stay UNSUPPORTED instead of a bogus package lookup).
NON_PACKAGE = {
    "weather",
    "joke",
    "capital",
    "restaurant",
    "today",
    "world",
    "cup",
    "spanish",
    "hello",
    "france",
    "french",
    "president",
    "stock",
    "game",
    "movie",
    "food",
    "coffee",
    "good",
    "favorite",
    "recommend",
    "translate",
}

VERSION_RE = re.compile(r"\d+\.\d+\.\d+(?:[-+][\w.-]+)?")
ADV_VERSION_RE = re.compile(r"adv-\d{4}-\d{2}[-_][\d.]+")
HANDLE_RE = re.compile(r"dev_[\w]+")
CUSTOMER_HANDLE_RE = re.compile(r"cust_[\w]+")

INTENT_KEYWORDS: list[tuple[set[str], IntentClass]] = [
    (
        {
            "typosquat",
            "typosquats",
            "typo",
            "squat",
            "lookalike",
            "similar",
            "doppelganger",
            "candidate",
            "candidates",
        },
        IntentClass.TYPOSQUAT_CANDIDATES,
    ),
    (
        {
            "resolved",
            "resolution",
            "resolutions",
            "while",
            "live",
            "lockfile",
            "lockfiles",
            "forensics",
            "forensic",
            "window",
            "pinned",
            "intake",
            "transfer",
            "moved",
            "during",
            "turnover",
            "turnovers",
        },
        IntentClass.RESOLVED_WHILE_LIVE,
    ),
    (
        {
            "maintainer",
            "maintainers",
            "maintained",
            "maintain",
            "maintains",
            "contagion",
            "contagious",
            "authored",
            "author",
            "share",
            "shared",
            "sharing",
            "owner",
            "owns",
            "owned",
            "own",
        },
        IntentClass.MAINTAINER_CONTAGION,
    ),
    (
        {
            "exposed",
            "exposure",
            "service",
            "services",
            "impacted",
            "reachable",
            "reach",
            "affected",
            "affect",
            "merchant",
            "merchants",
        },
        IntentClass.EXPOSED_SERVICES,
    ),
    (
        {
            "blast",
            "radius",
            "dependants",
            "dependents",
            "depends",
            "transitive",
            "transitively",
            "reverse",
            "closure",
            "impact",
        },
        IntentClass.BLAST_RADIUS,
    ),
    (
        {"lookup", "details", "describe", "version", "info", "information"},
        IntentClass.PACKAGE_LOOKUP,
    ),
]

# High-confidence signals per intent (weight 2). Weak keywords carry weight 1.
STRONG_KEYWORDS: dict[IntentClass, set[str]] = {
    IntentClass.TYPOSQUAT_CANDIDATES: {
        "typosquat",
        "typosquats",
        "typo",
        "squat",
        "lookalike",
        "doppelganger",
        "candidate",
        "candidates",
    },
    IntentClass.EXPOSED_SERVICES: {
        "exposed",
        "exposure",
        "impacted",
        "reachable",
        "affected",
        "service",
        "services",
        "merchant",
        "merchants",
    },
    IntentClass.RESOLVED_WHILE_LIVE: {
        "resolved",
        "lockfile",
        "lockfiles",
        "pinned",
        "intake",
        "transfer",
        "transferred",
        "moved",
        "turnover",
        "turnovers",
    },
    IntentClass.MAINTAINER_CONTAGION: {
        "maintainer",
        "maintainers",
        "maintained",
        "maintains",
        "maintain",
        "contagion",
        "contagious",
        "owner",
        "owns",
        "owned",
    },
    IntentClass.BLAST_RADIUS: {
        "blast",
        "radius",
        "dependants",
        "dependents",
        "transitive",
        "transitively",
        "reverse",
        "closure",
    },
    IntentClass.PACKAGE_LOOKUP: {"lookup", "details", "describe"},
}


def _tokens(text: str) -> list[str]:
    return re.findall(r"[\w-]+", text.lower())


def classify(question: str) -> QueryPlan:
    raw = question.strip()
    tokens = _tokens(raw)

    package: str | None = None
    version: str | None = None
    developer: str | None = None
    seed_names: list[str] = []

    # split package@version composites first
    for tok in list(tokens):
        if "@" in raw.lower():
            for part in re.findall(r"[\w-]+@[\w.-]+", raw.lower()):
                p, v = part.split("@", 1)
                package = package or p
                if VERSION_RE.fullmatch(v) or ADV_VERSION_RE.fullmatch(v):
                    version = v

    adv = ADV_VERSION_RE.search(raw.lower())
    if version is None and adv:
        version = adv.group(0)
    m = VERSION_RE.search(raw.lower())
    if version is None and m:
        version = m.group(0)

    for tok in tokens:
        if HANDLE_RE.fullmatch(tok) or CUSTOMER_HANDLE_RE.fullmatch(tok):
            developer = tok
            break
    if developer is None and tokens:
        for i, tok in enumerate(tokens):
            if tok in ("developer", "maintainer") and i + 1 < len(tokens):
                developer = tokens[i + 1]
                break

    non_keywords = {t for t, _ in INTENT_KEYWORDS for t in t}
    stop = STOPWORDS | non_keywords
    for tok in tokens:
        if tok in stop or tok == "live":
            continue
        if tok.isdigit():
            continue
        if VERSION_RE.fullmatch(tok) or ADV_VERSION_RE.fullmatch(tok):
            continue
        if tok in NON_PACKAGE:
            continue
        if tok == developer or (developer and tok.startswith(("dev_", "cust_"))):
            continue
        if tok in seed_names:
            continue
        seed_names.append(tok)
    if seed_names and package is None:
        package = seed_names[0]

    tok_set = set(tokens)
    # Score = 2 per strong keyword + 1 per weak keyword; ties break by catalog
    # order. Ambiguous phrasing ("during the intake window") no longer outranks a
    # strong signal ("which merchants were exposed").
    best: tuple[int, int] = (-1, -1)
    intent = IntentClass.UNSUPPORTED
    for i, (keywords, cls) in enumerate(INTENT_KEYWORDS):
        hits = keywords & tok_set
        if not hits:
            continue
        strong = len(STRONG_KEYWORDS[cls] & tok_set)
        score = 2 * strong + len(hits)  # len(hits) == weak count
        if (score, -i) > best:
            best = (score, -i)
            intent = cls
    if (
        intent == IntentClass.UNSUPPORTED
        and package
        and any(
            k in tok_set
            for k in ("what", "about", "lookup", "details", "describe", "tell")
        )
    ):
        intent = IntentClass.PACKAGE_LOOKUP

    return QueryPlan(
        intent=intent,
        package=package,
        version=version,
        developer=developer,
        seed_names=seed_names,
        raw=raw,
    )

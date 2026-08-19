"""Pydantic models for the Slash agent pipeline (deterministic, no LLM)."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class IntentClass(str, Enum):
    BLAST_RADIUS = "BLAST_RADIUS"
    EXPOSED_SERVICES = "EXPOSED_SERVICES"
    RESOLVED_WHILE_LIVE = "RESOLVED_WHILE_LIVE"
    MAINTAINER_CONTAGION = "MAINTAINER_CONTAGION"
    TYPOSQUAT_CANDIDATES = "TYPOSQUAT_CANDIDATES"
    PACKAGE_LOOKUP = "PACKAGE_LOOKUP"
    UNSUPPORTED = "UNSUPPORTED"


class QueryPlan(BaseModel):
    intent: IntentClass
    package: str | None = None
    version: str | None = None
    developer: str | None = None
    seed_names: list[str] = Field(default_factory=list)
    raw: str = ""


class Evidence(BaseModel):
    purpose: str
    cypher: str
    params: dict = Field(default_factory=dict)
    row_count: int = 0
    elapsed_ms: float = 0.0


class Verdict(BaseModel):
    intent: IntentClass
    answer: str = ""
    evidence_chain: list[Evidence] = Field(default_factory=list)
    abstain: bool = False
    reason: str = ""
    latency_ms: float = 0.0
    query_count: int = 0
    summary: str = ""  # optional LLM executive summary (ADR-0011); "" when off

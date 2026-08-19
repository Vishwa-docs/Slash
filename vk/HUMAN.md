# HUMAN.md — Optional resources we could use

Hi! These are **optional** — the product runs 100% without them (deterministic,
no keys, no network). They unlock premium/enterprise-adjacent polish for the
investor demo. Leave whatever you don't want to share; nothing depends on them.

## 1. GitHub token (encrypted/read-only) — unlocks: real-repo `slash scan`

`slash scan` currently scans a local directory of `package-lock.json` files
against the graph. With a read-only PAT we can also scan **any public repo by
URL** (clone-on-the-fly) and—down the line—a GitHub App bot that comments on PRs
that add dependencies (the Socket.dev "PR report" moment).

> `gh auth token` ✔ or create a fine-grained PAT with **Read access to Public
> repositories + Metadata**.

## 2. LLM API key (any OpenAI-compatible endpoint) — unlocks: human-language digests

The pipeline is fully deterministic (that's the trust story). An LLM is only ever
an *optional garnish*, OFF by default, validated by Pydantic, never allowed to
change an answer (registry: `cap.llm.optional`, quarantined). If you give us a key
we can add:
- **Weekly digest narrations** — the snapshot→delta report rewritten into a
  board-ready paragraph a CISO can forward.
- **PR-comment drafting** — human-readable descriptions of each violation.

Provide either `OPENAI_API_KEY` or a custom `LLM_BASE_URL` + `LLM_API_KEY`.

## 3. Nothing else

We deliberately want no SaaS account, no vendor telemetry, no upload. The
"self-hosted, no-token, your graph stays yours" story is a core differentiator
vs Socket.dev/Snyk.

## What to decide if you want them

Put them in an untracked `.env` (or tell me and I'll wire a
`.env.example` + `scripts/monitor.py --narrate` off-by-default path):

```
GITHUB_TOKEN=                  # optional: public-repo scan
LLM_BASE_URL=                  # optional: default https://api.openai.com/v1
LLM_API_KEY=                   # optional: digest narration
```
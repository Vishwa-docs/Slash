# Product Outcomes & Success Metrics

> Source of truth: `vl/PLAN.md` §1 and §4.

## Target outcomes (what "winning" means to us)
1. **Best Use of HydraDB** is the achievable headline prize: a data model + traversal that a
   vector database physically cannot reproduce, shown in demo and README.
2. **Track 02 winner** / Grand Champion: we are judged on technical execution, product
   completeness, quality of results, and originality — all covered by F1–F8 + S1–S6.
3. **A venture/portfolio-credible artifact**: even without a prize, the repo demonstrates a
   defensible supply-chain-security product core on a novel database.

## Metrics we report (no fabrication, per evidence rule)
| Metric | Where it comes from | Target |
|---|---|---|
| Precision / recall / F1 on held-out advisories | `.evidence/runs/phase-6/eval.txt` | reported, high |
| Query latency p95 | client `elapsed_ms` in integration tests | < 1 s |
| Queries-per-question + (LLM off ⇒ 0 tokens) cost | eval harness | reported |
| Reproduce time (clean clone → demo) | Phase 6 clean-clone run | < 2 min |
| Abstention correctness | unit suite (5/5 abstain) | 100% |

## Anti-outcomes (explicitly not OK)
- Claiming benchmark numbers without `.evidence/` behind them.
- Faking a HydraDB capability the live container does not have.
- Shipping a slick UI with no real graph traversal (the whole point is the graph).
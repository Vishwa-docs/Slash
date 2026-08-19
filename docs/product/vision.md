# Product Vision

> Source of truth: `vl/PLAN.md` and `docs/reference/strategy-analysis.md`.

## The problem
Software supply chain attacks are automated, self-propagating worms. In the TanStack compromise,
84 malicious artifacts hit 42 packages within six minutes of a CI breach, then spread through
`.claude/` and `.vscode/` and survived `npm uninstall`. The defender's problem is **speed and
topology**: when a package is compromised at 09:00, which of your services are exposed by 09:06?
That is a transitive reverse-dependency closure over an ecosystem graph — a topological question
a vector index cannot answer at all.

## The product
Slash is a real-time blast-radius intelligence console for the software supply chain,
powered by **HydraDB**. It holds a full package ecosystem as a graph and answers, in seconds or
better, with a traceable evidence chain:

1. **Which internal services are transitively exposed** by a compromised package?
2. **Which apps resolved the bad version while it was live** (forensic temporal resolution)?
3. **Which packages share maintainers / infrastructure** with the compromised one (contagion)?
4. **Which nearby names are likely typosquats** (reputational + name-similarity)? 
5. **What is the complete blast radius?**

…and it **abstains honestly** when the answer isn't in the graph.

## North star
One demo sentence a judge remembers:

> "Type the package name, see the exact traversal HydraDB ran, the exposed services, the
> lockfiles that resolved the bad version while it was live, and the typosquats sitting
> next to it — with every claim backed by a query — in under a second."

## Non-goals (what we are deliberately NOT building)
- No general chat over arbitrary documents (that's Track 01/03 territory).
- No vector retrieval — if a feature is just semantic search, it is out of scope.
- No production SIEM integration; this is a demonstrable, extensible core.
- No code-graph-for-IDEs (Track 02B) — we chose option A (supply chain).
- No exhaustive npm mirror; we run a representative, reproducible ecosystem graph and document
  how the pipeline scales to the full registry.
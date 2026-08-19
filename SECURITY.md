# Security Policy

This is a hackathon demo. Scope of the policy: keep the repo safe to open and the demo honest.

## Reporting
If you find a real vulnerability in this project (as opposed to the synthetic demo),
open a GitHub issue. Do **not** file a report for the planted "advisories" — those are
dataset fixtures, not bugs.

## Hard rules
- No secrets or tokens in the repo. Local token file lives outside `.git` (`.gitignore`d).
- No user text is ever interpolated into Cypher — all queries are parameterized.
- No production data, credentials, or real customer information in code, logs, or docs.
- If you discover a flaw that would embarrass the submission, fix it or drop the feature —
  never fake the result.

## Securing the demo box
- HydraDB runs on `127.0.0.1` with `GRAPH_ALLOW_PLAINTEXT=true` (intentional for localhost).
- Do not expose ports 7687/8443/9090 to a public interface.
- The Streamlit app binds locally by default (`streamlit run app.py`).
## Phase 4 — Evaluation and CI/CD

A 10-case evaluation dataset tests answer accuracy, citation compliance,
and refusal behavior using a RAGAS-inspired harness. Results are written
to eval_report.json. GitHub Actions runs this harness on every push and
fails the build if scores drop below threshold — enforcing production
quality on every commit.

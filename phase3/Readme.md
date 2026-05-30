## Phase 3 — Observability and Logging

Every query is logged to SQLite and JSONL with per-stage latency breakdown
(retrieval, reranking, generation). An analytics dashboard displays query
history, average latency trends, and refusal rates from the terminal.

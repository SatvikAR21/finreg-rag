## Phase 2 — Hybrid Retrieval and Generation

Combines BM25 keyword search with ChromaDB vector search using Reciprocal
Rank Fusion. Results are reranked by Cohere's cross-encoder. A YAML-managed
prompt enforces citation markers [1][2] in every generated answer. The
citation_enforcer module validates compliance before returning responses.

# =============================================================================
# What this file does:
# The main interactive query loop for FinReg-RAG v3 — the complete production
# pipeline. Ties together Phase 2 (hybrid retrieval + reranking + cited 
# generation + YAML prompts) with Phase 3 (SQLite + JSONL logging + latency
# tracking). Every query is timed at each stage and logged automatically.
#
# Run this file to use the system interactively:
#   python phase3/query_v3.py
# =============================================================================

import sys          # for modifying Python's module search path
import os           # for path manipulation
import time         # for measuring latency with perf_counter

# --- PATH SETUP ---
# We need Python to find modules in both phase2/ and phase3/ folders.
# sys.path is the list of folders Python searches when you do "import something".
# We add the project root and both phase folders to that list.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # FinReg/ folder
sys.path.insert(0, _PROJECT_ROOT)                    # add project root to path
sys.path.insert(0, os.path.join(_PROJECT_ROOT, "phase2"))  # add phase2/ to path
sys.path.insert(0, os.path.join(_PROJECT_ROOT, "phase3"))  # add phase3/ to path

# --- IMPORTS FROM PHASE 2 ---
from hybrid_retriever import hybrid_search           # Step 1: BM25 + vector search
from reranker import rerank_chunks                   # Step 2: Cohere reranking
from citation_enforcer import generate_cited_answer  # Step 3: cited LLM generation
from prompt_loader import get_model_config           # YAML config loader

# --- IMPORTS FROM PHASE 3 ---
from logger import QueryLogger                       # our SQLite + JSONL logger


def run_pipeline(query, logger):
    """
    Runs one query through the complete FinReg-RAG pipeline with timing.
    
    Stages:
        1. Hybrid retrieval (BM25 + vector + RRF)
        2. Cohere reranking
        3. Cited answer generation
        4. Logging to SQLite + JSONL
    
    Args:
        query: the user's question string
        logger: a QueryLogger instance for recording results
    
    Returns:
        The result dict from generate_cited_answer()
    """
    print("\n" + "─" * 60)          # visual separator between queries

    # ── STAGE 1: HYBRID RETRIEVAL ──────────────────────────────
    t0 = time.perf_counter()                              # start retrieval timer
    hybrid_chunks = hybrid_search(query, top_k=5)         # run BM25 + vector + RRF
    retrieval_ms = (time.perf_counter() - t0) * 1000     # convert seconds to milliseconds

    # ── STAGE 2: COHERE RERANKING ──────────────────────────────
    t1 = time.perf_counter()                              # start reranking timer
    reranked = rerank_chunks(query, hybrid_chunks, top_n=3)  # rerank to top 3
    rerank_ms = (time.perf_counter() - t1) * 1000        # convert to milliseconds

    # ── STAGE 3: CITED ANSWER GENERATION ───────────────────────
    t2 = time.perf_counter()                              # start generation timer
    result = generate_cited_answer(query, reranked)       # generate cited answer
    generation_ms = (time.perf_counter() - t2) * 1000    # convert to milliseconds

    # ── STAGE 4: LOGGING ────────────────────────────────────────
    model_config = get_model_config()                     # load YAML config for metadata
    logger.log_query(                                     # write to SQLite + JSONL
        query=query,
        answer=result["answer"],
        chunks_used=result["chunks_used"],
        refused=result["refused"],
        retrieval_latency_ms=retrieval_ms,
        rerank_latency_ms=rerank_ms,
        generation_latency_ms=generation_ms,
        prompt_version=model_config.get("prompt_version", "2.0"),
        model_used=model_config.get("model", "llama-3.3-70b-versatile")
    )

    # ── PRINT RESULTS ───────────────────────────────────────────
    total_ms = retrieval_ms + rerank_ms + generation_ms   # calculate total time

    print("\n📋 ANSWER:")
    print("─" * 60)
    print(result["answer"])                               # print the cited answer
    print("─" * 60)

    # Print timing breakdown
    print(f"\n⏱  LATENCY BREAKDOWN:")
    print(f"   Retrieval  : {retrieval_ms:>7.0f}ms")     # hybrid search time
    print(f"   Reranking  : {rerank_ms:>7.0f}ms")        # Cohere reranking time
    print(f"   Generation : {generation_ms:>7.0f}ms")    # LLM generation time
    print(f"   ─────────────────────")
    print(f"   TOTAL      : {total_ms:>7.0f}ms")         # end-to-end time

    if result["refused"]:                                 # if system refused to answer
        print("\n⚠️  REFUSAL: Insufficient source material for this query.")

    return result                                         # return for any downstream use


def print_welcome():
    """Prints the welcome banner when the interactive loop starts."""
    print("\n" + "=" * 60)
    print("   FINREG-RAG v3 — Production Query Interface")
    print("   Hybrid Retrieval | Cohere Reranking | Citations")
    print("   Logging: SQLite + JSONL")
    print("=" * 60)
    print("  Type your regulatory question and press Enter.")
    print("  Commands:")
    print("    'exit'      — quit the program")
    print("    'stats'     — show analytics dashboard")
    print("    'help'      — show example questions")
    print("=" * 60)


def print_help():
    """Prints example questions the user can try."""
    print("\n💡 EXAMPLE QUESTIONS TO TRY:")
    examples = [
        "What is the minimum CET1 capital ratio under Basel III?",
        "What is the capital conservation buffer requirement?",
        "How does Basel III define Tier 1 capital?",
        "What are the liquidity coverage ratio requirements?",
        "What is the leverage ratio requirement under Basel III?",
        "How are risk-weighted assets calculated?",
        "What is the countercyclical capital buffer?",
    ]
    for i, q in enumerate(examples, 1):                  # print numbered list
        print(f"  {i}. {q}")
    print()


def main():
    """Main interactive loop — runs until user types 'exit'."""
    print_welcome()                                       # show banner

    # Import analytics here to avoid circular imports at module level
    from analytics import run_full_report                 # analytics dashboard function

    logger = QueryLogger()                                # initialize logger (creates DB if needed)
    print("\n✅ System ready. All components loaded.\n")

    query_count = 0                                       # track queries this session

    while True:                                           # loop forever until 'exit'
        try:
            # Get input from user
            user_input = input("🔍 Your question: ").strip()  # read and clean input

            if not user_input:                            # empty input — just skip
                continue

            if user_input.lower() == "exit":             # user wants to quit
                print(f"\n👋 Session ended. {query_count} queries processed this session.")
                print("Run 'python phase3/analytics.py' to see your full query history.\n")
                break                                     # exit the loop

            if user_input.lower() == "stats":            # user wants analytics
                run_full_report()                         # print the dashboard
                continue                                  # go back to waiting for input

            if user_input.lower() == "help":             # user wants examples
                print_help()                              # print example questions
                continue

            # Run the full pipeline for a real query
            query_count += 1                              # increment session counter
            print(f"\n[Query #{query_count} this session]")
            run_pipeline(user_input, logger)              # run the full pipeline

        except KeyboardInterrupt:                         # user pressed Ctrl+C
            print("\n\n👋 Interrupted. Exiting.\n")
            break                                         # exit cleanly

        except Exception as e:                            # any unexpected error
            print(f"\n❌ Error processing query: {e}")    # show the error
            print("Please try again or type 'exit' to quit.\n")
            continue                                      # keep the loop running


# --- ENTRY POINT ---
if __name__ == "__main__":
    main()                                                # run the interactive loop
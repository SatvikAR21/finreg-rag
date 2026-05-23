# =============================================================================
# What this file does:
# Automated evaluation harness for the FinReg-RAG system. Loads test cases
# from eval_dataset.json, runs each question through the full pipeline,
# scores results on three dimensions (answer correctness, citation compliance,
# refusal accuracy), prints a detailed report, and saves results to JSON.
#
# Run with: python phase4/evaluator.py
# This is also what GitHub Actions runs automatically on every code push.
# =============================================================================

import sys           # for modifying Python's module search path
import os            # for file path operations
import json          # for reading/writing JSON files
import time          # for measuring evaluation time
from datetime import datetime, timezone   # for timestamps

# --- PATH SETUP ---
# Add project root and phase folders to Python's search path
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _PROJECT_ROOT)
sys.path.insert(0, os.path.join(_PROJECT_ROOT, "phase2"))
sys.path.insert(0, os.path.join(_PROJECT_ROOT, "phase3"))

# --- IMPORTS ---
from hybrid_retriever import hybrid_search           # BM25 + vector retrieval
from reranker import rerank_chunks                   # Cohere reranking
from citation_enforcer import generate_cited_answer  # cited LLM generation

# --- CONFIGURATION ---
DATASET_PATH = os.path.join("phase4", "eval_dataset.json")       # test cases
REPORT_PATH = os.path.join("phase4", "eval_report.json")         # output report
PASS_THRESHOLD = 0.70          # system passes if overall score >= 70%


def load_dataset():
    """Loads and returns the list of test cases from eval_dataset.json."""
    with open(DATASET_PATH, "r", encoding="utf-8") as f:   # open dataset file
        return json.load(f)                                  # parse and return


def score_answer(result, test_case):
    """
    Scores one pipeline result against its test case on three dimensions.

    Dimension 1 — Keyword Coverage (0.0 to 1.0):
        What fraction of expected_keywords appear in the answer?
        Full credit = all keywords found. Partial credit for partial matches.

    Dimension 2 — Citation Compliance (0.0 or 1.0):
        Does the answer contain at least one citation marker like [1], [2]?
        Binary — either it cited or it didn't.

    Dimension 3 — Refusal Accuracy (0.0 or 1.0):
        If we expected a refusal, did it refuse? If we expected an answer, did it answer?
        Binary — either the refusal behavior matched expectation or it didn't.

    Returns a dict with individual scores and an overall weighted score.
    """
    answer = result["answer"].lower()          # lowercase for case-insensitive matching
    refused = result["refused"]                # True if system refused to answer
    expected_keywords = test_case["expected_keywords"]   # list of required phrases
    expect_refusal = test_case["expect_refusal"]         # True if refusal is correct

    # --- Dimension 1: Keyword Coverage ---
    if expect_refusal:                         # if refusal expected, keywords don't apply
        keyword_score = 1.0 if refused else 0.0  # full credit for correct refusal
    elif not expected_keywords:                # no keywords defined — neutral
        keyword_score = 0.5
    else:
        # Count how many expected keywords appear in the answer
        hits = sum(                            # sum up keyword matches
            1 for kw in expected_keywords      # for each expected keyword
            if kw.lower() in answer            # check if it appears in answer
        )
        keyword_score = hits / len(expected_keywords)  # fraction found

    # --- Dimension 2: Citation Compliance ---
    if expect_refusal:                         # refusal answers don't need citations
        citation_score = 1.0 if refused else 0.0
    else:
        # Check if any citation marker [1], [2], [3] appears in the answer
        has_citation = any(
            f"[{i}]" in result["answer"]       # look for [1], [2], [3] in original case
            for i in range(1, 6)               # check [1] through [5]
        )
        citation_score = 1.0 if has_citation else 0.0   # binary score

    # --- Dimension 3: Refusal Accuracy ---
    refusal_correct = (refused == expect_refusal)        # did behavior match expectation?
    refusal_score = 1.0 if refusal_correct else 0.0      # binary score

    # --- Overall weighted score ---
    # Keywords: 50% weight (most important — did we get the right facts?)
    # Citations: 30% weight (compliance requirement)
    # Refusal:  20% weight (safety behavior)
    overall = (keyword_score * 0.50) + (citation_score * 0.30) + (refusal_score * 0.20)

    return {
        "keyword_score": round(keyword_score, 3),    # fraction of keywords found
        "citation_score": round(citation_score, 3),  # 0 or 1
        "refusal_score": round(refusal_score, 3),    # 0 or 1
        "overall_score": round(overall, 3),          # weighted combination
        "passed": overall >= PASS_THRESHOLD,         # True if this test case passed
        "keywords_found": [                          # which keywords were found
            kw for kw in expected_keywords
            if kw.lower() in answer
        ],
        "keywords_missing": [                        # which keywords were missing
            kw for kw in expected_keywords
            if kw.lower() not in answer
        ]
    }


def run_evaluation():
    """
    Runs all test cases through the pipeline, scores each one,
    prints a detailed report, and saves results to eval_report.json.
    Returns True if the overall system passes, False if it fails.
    """
    print("\n" + "=" * 65)
    print("   FINREG-RAG EVALUATION HARNESS")
    print(f"   Running {10} test cases against the full pipeline")
    print("=" * 65)

    dataset = load_dataset()                   # load all test cases
    results = []                               # list to collect all scored results
    eval_start = time.perf_counter()           # start total evaluation timer

    for i, test_case in enumerate(dataset):    # loop through each test case
        tc_id = test_case["id"]
        topic = test_case["topic"]
        question = test_case["question"]

        print(f"\n[{i+1:02d}/{len(dataset)}] {tc_id} — {topic}")
        print(f"  Q: {question[:70]}{'...' if len(question) > 70 else ''}")

        # --- Run the full pipeline ---
        try:
            t0 = time.perf_counter()                              # start timer

            hybrid_chunks = hybrid_search(question, top_k=5)     # retrieve
            reranked = rerank_chunks(question, hybrid_chunks, top_n=3)  # rerank
            result = generate_cited_answer(question, reranked)    # generate

            latency_ms = (time.perf_counter() - t0) * 1000       # measure time
            result["latency_ms"] = latency_ms                     # attach latency

            # --- Score the result ---
            scores = score_answer(result, test_case)              # score it

            # --- Print inline result ---
            status = "✅ PASS" if scores["passed"] else "❌ FAIL"
            print(f"  {status} | Overall: {scores['overall_score']:.2f} | "
                  f"Keywords: {scores['keyword_score']:.2f} | "
                  f"Citations: {scores['citation_score']:.2f} | "
                  f"Refusal: {scores['refusal_score']:.2f} | "
                  f"Latency: {latency_ms:.0f}ms")

            if scores["keywords_missing"]:                        # show missing keywords
                print(f"  ⚠️  Missing keywords: {scores['keywords_missing']}")

            # Build the full result record
            results.append({
                "test_case": test_case,
                "answer": result["answer"],
                "refused": result["refused"],
                "scores": scores,
                "latency_ms": round(latency_ms, 0),
                "chunks_used": len(result["chunks_used"])
            })

        except Exception as e:                                    # catch any pipeline error
            print(f"  ❌ ERROR: {e}")
            results.append({
                "test_case": test_case,
                "answer": f"PIPELINE ERROR: {str(e)}",
                "refused": False,
                "scores": {
                    "keyword_score": 0.0, "citation_score": 0.0,
                    "refusal_score": 0.0, "overall_score": 0.0, "passed": False,
                    "keywords_found": [], "keywords_missing": test_case["expected_keywords"]
                },
                "latency_ms": 0,
                "chunks_used": 0
            })

    # --- Aggregate results ---
    total_eval_time = (time.perf_counter() - eval_start) * 1000  # total time in ms
    total_cases = len(results)                                    # how many test cases
    passed_cases = sum(1 for r in results if r["scores"]["passed"])  # how many passed
    pass_rate = passed_cases / total_cases if total_cases > 0 else 0  # pass rate

    avg_overall = sum(r["scores"]["overall_score"] for r in results) / total_cases
    avg_keyword = sum(r["scores"]["keyword_score"] for r in results) / total_cases
    avg_citation = sum(r["scores"]["citation_score"] for r in results) / total_cases
    avg_refusal = sum(r["scores"]["refusal_score"] for r in results) / total_cases
    avg_latency = sum(r["latency_ms"] for r in results) / total_cases

    system_passed = pass_rate >= PASS_THRESHOLD                  # did system pass overall?

    # --- Print summary ---
    print("\n" + "=" * 65)
    print("   EVALUATION SUMMARY")
    print("=" * 65)
    print(f"  Test cases run      : {total_cases}")
    print(f"  Passed              : {passed_cases} / {total_cases}")
    print(f"  Pass rate           : {pass_rate*100:.1f}%")
    print(f"  ─────────────────────────────────────────")
    print(f"  Avg keyword score   : {avg_keyword:.3f}  (target facts found)")
    print(f"  Avg citation score  : {avg_citation:.3f}  (sources cited)")
    print(f"  Avg refusal score   : {avg_refusal:.3f}  (refusal behavior)")
    print(f"  Avg overall score   : {avg_overall:.3f}")
    print(f"  ─────────────────────────────────────────")
    print(f"  Avg latency         : {avg_latency:.0f}ms per query")
    print(f"  Total eval time     : {total_eval_time/1000:.1f}s")
    print(f"\n  SYSTEM STATUS: {'✅ PASSED' if system_passed else '❌ FAILED'}")
    print(f"  (Pass threshold: {PASS_THRESHOLD*100:.0f}% overall score)")
    print("=" * 65)

    # --- Save report to JSON ---
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "system_passed": system_passed,
        "pass_rate": round(pass_rate, 3),
        "total_cases": total_cases,
        "passed_cases": passed_cases,
        "averages": {
            "overall": round(avg_overall, 3),
            "keyword": round(avg_keyword, 3),
            "citation": round(avg_citation, 3),
            "refusal": round(avg_refusal, 3),
            "latency_ms": round(avg_latency, 0)
        },
        "results": results
    }

    with open(REPORT_PATH, "w", encoding="utf-8") as f:    # save report
        json.dump(report, f, indent=2)                      # pretty-print JSON

    print(f"\n  📄 Full report saved to: {REPORT_PATH}")

    return system_passed                                    # return pass/fail for CI


# --- ENTRY POINT ---
if __name__ == "__main__":
    passed = run_evaluation()                               # run the evaluation
    sys.exit(0 if passed else 1)                           # exit code for CI: 0=pass, 1=fail
# =============================================================================
# What this file does:
# Reads the finreg_queries.db SQLite database and prints a clean performance
# analytics report to the terminal. Shows query counts, latency breakdowns,
# refusal rates, slowest queries, and most frequently cited sources.
# Run this any time to see how your RAG system is performing.
# =============================================================================

import sqlite3      # built-in Python SQLite library
import json         # for parsing the chunk_sources JSON strings
import os           # for building file paths

# --- CONFIGURATION ---
DB_PATH = os.path.join("logs", "finreg_queries.db")    # path to our SQLite database


def get_connection():
    """Opens and returns a SQLite database connection."""
    if not os.path.exists(DB_PATH):                    # check database exists
        raise FileNotFoundError(
            f"Database not found at {DB_PATH}. Run phase3/logger.py first."
        )
    return sqlite3.connect(DB_PATH)                    # return open connection


def print_separator(title=""):
    """Prints a clean section separator line."""
    if title:                                          # if a title was given
        print(f"\n{'='*20} {title} {'='*20}")         # print titled separator
    else:
        print("=" * 60)                                # print plain separator


def report_overview(cursor):
    """Prints high-level query counts and refusal rate."""
    print_separator("OVERVIEW")

    # Total number of queries logged
    cursor.execute("SELECT COUNT(*) FROM queries")             # count all rows
    total = cursor.fetchone()[0]                               # get the number

    # Number of refused queries
    cursor.execute("SELECT COUNT(*) FROM queries WHERE refused = 1")  # count refusals
    refused = cursor.fetchone()[0]                             # get the number

    # Number of answered queries
    answered = total - refused                                 # subtract refusals

    # Refusal rate as a percentage
    refusal_rate = (refused / total * 100) if total > 0 else 0  # avoid divide by zero

    print(f"  Total queries logged : {total}")
    print(f"  Answered             : {answered}")
    print(f"  Refused              : {refused}")
    print(f"  Refusal rate         : {refusal_rate:.1f}%")


def report_latency(cursor):
    """Prints average, min, and max latency for each pipeline stage."""
    print_separator("LATENCY (milliseconds)")

    # Query average, min, max for each latency column
    cursor.execute("""
        SELECT
            AVG(retrieval_latency_ms),    -- average retrieval time
            MIN(retrieval_latency_ms),    -- fastest retrieval
            MAX(retrieval_latency_ms),    -- slowest retrieval
            AVG(rerank_latency_ms),       -- average reranking time
            MIN(rerank_latency_ms),       -- fastest reranking
            MAX(rerank_latency_ms),       -- slowest reranking
            AVG(generation_latency_ms),   -- average LLM generation time
            MIN(generation_latency_ms),   -- fastest generation
            MAX(generation_latency_ms),   -- slowest generation
            AVG(total_latency_ms),        -- average end-to-end time
            MIN(total_latency_ms),        -- fastest end-to-end
            MAX(total_latency_ms)         -- slowest end-to-end
        FROM queries
        WHERE refused = 0                 -- only include answered queries
    """)
    row = cursor.fetchone()              # get the single result row

    if row[0] is None:                   # no answered queries yet
        print("  No answered queries to report latency for.")
        return

    # Print a formatted table of latency stats
    print(f"  {'Stage':<25} {'Avg':>8} {'Min':>8} {'Max':>8}")
    print(f"  {'-'*50}")
    print(f"  {'Retrieval (hybrid)':<25} {row[0]:>7.0f}ms {row[1]:>7.0f}ms {row[2]:>7.0f}ms")
    print(f"  {'Reranking (Cohere)':<25} {row[3]:>7.0f}ms {row[4]:>7.0f}ms {row[5]:>7.0f}ms")
    print(f"  {'Generation (LLM)':<25} {row[6]:>7.0f}ms {row[7]:>7.0f}ms {row[8]:>7.0f}ms")
    print(f"  {'-'*50}")
    print(f"  {'TOTAL end-to-end':<25} {row[9]:>7.0f}ms {row[10]:>7.0f}ms {row[11]:>7.0f}ms")


def report_chunk_quality(cursor):
    """Prints average Cohere relevance scores across all queries."""
    print_separator("CHUNK QUALITY (Cohere Scores)")

    cursor.execute("""
        SELECT
            AVG(top_chunk_score),     -- average best-chunk relevance score
            MIN(top_chunk_score),     -- lowest best-chunk score seen
            MAX(top_chunk_score),     -- highest best-chunk score seen
            AVG(chunks_retrieved)     -- average number of chunks used per query
        FROM queries
        WHERE refused = 0             -- only answered queries
    """)
    row = cursor.fetchone()           # get the result row

    if row[0] is None:
        print("  No data available yet.")
        return

    print(f"  Avg top chunk score  : {row[0]:.4f}")   # e.g. 0.9800
    print(f"  Min top chunk score  : {row[1]:.4f}")   # lowest we've seen
    print(f"  Max top chunk score  : {row[2]:.4f}")   # highest we've seen
    print(f"  Avg chunks per query : {row[3]:.1f}")   # usually 2-3


def report_slowest_queries(cursor, n=5):
    """Prints the N slowest queries by total latency."""
    print_separator(f"SLOWEST {n} QUERIES")

    cursor.execute("""
        SELECT query, total_latency_ms, timestamp   -- get question, time, and when
        FROM queries
        WHERE refused = 0                           -- only answered queries
        ORDER BY total_latency_ms DESC              -- slowest first
        LIMIT ?                                     -- only top N
    """, (n,))                                      # pass n as parameter
    rows = cursor.fetchall()                        # get all result rows

    if not rows:
        print("  No data available yet.")
        return

    for i, row in enumerate(rows):                  # loop through results
        query_preview = row[0][:55] + "..." if len(row[0]) > 55 else row[0]  # truncate long queries
        print(f"  {i+1}. [{row[1]:>6.0f}ms] {query_preview}")               # print with latency


def report_top_sources(cursor, n=10):
    """Prints the most frequently cited source documents and pages."""
    print_separator("MOST CITED SOURCES")

    cursor.execute("SELECT chunk_sources FROM queries WHERE refused = 0")  # get all source lists
    rows = cursor.fetchall()                         # get all rows

    if not rows:
        print("  No data available yet.")
        return

    source_counts = {}                               # dict to count citation frequency
    for row in rows:                                 # loop through each query's sources
        try:
            sources = json.loads(row[0])             # parse the JSON string back to a list
            for source in sources:                   # loop through each source reference
                source_counts[source] = source_counts.get(source, 0) + 1  # increment count
        except (json.JSONDecodeError, TypeError):    # handle any malformed data
            continue                                 # skip bad records

    if not source_counts:                            # nothing to show
        print("  No source data available.")
        return

    # Sort by count descending and show top N
    sorted_sources = sorted(source_counts.items(), key=lambda x: x[1], reverse=True)
    for source, count in sorted_sources[:n]:         # show top N sources
        print(f"  {count:>3}x  {source}")            # e.g. "  7x  basel3.pdf:p28"


def report_recent_queries(cursor, n=5):
    """Prints the most recent N queries with their answers."""
    print_separator(f"RECENT {n} QUERIES")

    cursor.execute("""
        SELECT query, answer, total_latency_ms, refused, timestamp
        FROM queries
        ORDER BY id DESC        -- most recent first (highest ID = most recent insert)
        LIMIT ?
    """, (n,))
    rows = cursor.fetchall()    # get results

    if not rows:
        print("  No queries logged yet.")
        return

    for i, row in enumerate(rows):                             # loop through results
        status = "REFUSED" if row[3] else "ANSWERED"          # human-readable status
        query_preview = row[0][:60] + "..." if len(row[0]) > 60 else row[0]
        answer_preview = row[1][:80] + "..." if len(row[1]) > 80 else row[1]
        print(f"\n  {i+1}. [{status}] {row[4][:19]}")         # timestamp
        print(f"     Q: {query_preview}")                      # question
        print(f"     A: {answer_preview}")                     # answer preview
        print(f"     Latency: {row[2]:.0f}ms")                 # response time


def run_full_report():
    """Runs all analytics sections and prints the complete dashboard."""
    print("\n" + "=" * 60)
    print("   FINREG-RAG OBSERVABILITY DASHBOARD")
    print("=" * 60)

    conn = get_connection()          # open database connection
    cursor = conn.cursor()           # create cursor

    report_overview(cursor)          # section 1: counts and refusal rate
    report_latency(cursor)           # section 2: latency breakdown
    report_chunk_quality(cursor)     # section 3: Cohere score stats
    report_slowest_queries(cursor)   # section 4: slowest queries
    report_top_sources(cursor)       # section 5: most cited pages
    report_recent_queries(cursor)    # section 6: recent query log

    conn.close()                     # close database connection
    print("\n" + "=" * 60)
    print("   END OF REPORT")
    print("=" * 60 + "\n")


# --- RUN ---
if __name__ == "__main__":
    run_full_report()                # print the full dashboard
# =============================================================================
# What this file does:
# Builds a citation-enforced prompt from reranked chunks, sends it to the
# Groq LLM, and returns a structured answer where every claim is backed by
# a numbered source reference. If the chunks don't contain the answer,
# the LLM is instructed to refuse rather than hallucinate.
# =============================================================================

import os                            # for reading environment variables
from groq import Groq                # Groq SDK for LLM generation
from dotenv import load_dotenv       # for loading .env file

load_dotenv()                        # load GROQ_API_KEY from .env

# --- CONFIGURATION ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")        # read Groq key from environment
LLM_MODEL = "llama-3.3-70b-versatile"           # same model used in Phase 1
MAX_TOKENS = 1024                                # maximum tokens in the response
COHERE_SCORE_THRESHOLD = 0.40                    # reject chunks below this relevance score


def build_cited_prompt(query, reranked_chunks):
    """
    Builds a structured prompt where each chunk is numbered [1], [2], [3].
    The system message instructs the LLM to cite every claim using these numbers
    and to refuse if the answer is not in the provided sources.
    
    Returns:
        system_message (str): strict citation instructions for the LLM
        user_message (str): the query + numbered source chunks
    """
    # --- Filter out low-confidence chunks ---
    filtered_chunks = [                                      # keep only high-quality chunks
        chunk for chunk in reranked_chunks                   # loop through all chunks
        if chunk.get("cohere_score", 1.0) >= COHERE_SCORE_THRESHOLD  # apply score threshold
    ]

    if not filtered_chunks:                                  # if nothing passes the filter
        return None, None                                    # signal that we should refuse

    # --- Build the numbered source block ---
    source_block = ""                                        # empty string to build into
    for i, chunk in enumerate(filtered_chunks):             # number each chunk starting at 1
        source_num = i + 1                                   # human-readable number (1, 2, 3)
        source = chunk.get("source", "Unknown document")    # document name from metadata
        page = chunk.get("page", "?")                       # page number from metadata
        # Also check inside nested metadata dict if present
        if source == "Unknown document" and "metadata" in chunk:
            source = chunk["metadata"].get("source", "Unknown document")
            page = chunk["metadata"].get("page", page)
        text = chunk["text"].strip()                         # clean the chunk text
        source_block += f"[{source_num}] Source: {source} | Page: {page}\n"  # source header
        source_block += f"{text}\n\n"                        # chunk text with spacing

    # --- System message: strict citation rules ---
    system_message = """You are a financial regulatory expert assistant with strict citation requirements.

RULES YOU MUST FOLLOW WITHOUT EXCEPTION:
1. Answer ONLY using information from the numbered source chunks provided below.
2. Every sentence in your answer MUST include a citation in the format [1], [2], or [3].
3. If the provided sources do not contain enough information to answer the question, respond ONLY with: "INSUFFICIENT SOURCE MATERIAL: The provided regulatory documents do not contain enough information to answer this question reliably."
4. Do NOT add any information from your general knowledge — only cite the provided sources.
5. Do NOT speculate or infer beyond what the sources explicitly state.
6. End your answer with a "Sources Used:" section listing each citation number, its document name, and page number.

Your answers will be used in financial compliance contexts. Accuracy and traceability are mandatory."""

    # --- User message: query + numbered chunks ---
    user_message = f"""QUESTION: {query}

SOURCE DOCUMENTS:
{source_block}

Provide a precise, cited answer using only the source documents above."""

    return system_message, user_message                      # return both message parts


def generate_cited_answer(query, reranked_chunks):
    """
    Full pipeline: builds cited prompt → sends to Groq → returns structured answer.
    
    Args:
        query: the user's question string
        reranked_chunks: list of chunk dicts from reranker.rerank_chunks()
    
    Returns:
        dict with keys: 'answer', 'chunks_used', 'refused', 'query'
    """
    if not GROQ_API_KEY:                                     # verify key exists
        raise ValueError("GROQ_API_KEY not found in .env file")

    print("  → Building citation-enforced prompt...")        # progress message

    system_msg, user_msg = build_cited_prompt(query, reranked_chunks)  # build prompt

    # --- Handle case where no chunks passed the quality threshold ---
    if system_msg is None:
        print("  ⚠️  All chunks below confidence threshold — refusing to answer")
        return {
            "query": query,                                  # echo the original query
            "answer": "INSUFFICIENT SOURCE MATERIAL: No retrieved chunks met the minimum relevance threshold. Please rephrase your question or check that the relevant document has been ingested.",
            "chunks_used": [],                               # no chunks used
            "refused": True                                  # flag that we refused
        }

    print("  → Sending to Groq LLM for generation...")       # progress message

    client = Groq(api_key=GROQ_API_KEY)                     # create Groq client

    response = client.chat.completions.create(              # call the LLM
        model=LLM_MODEL,                                    # which model to use
        messages=[                                          # conversation structure
            {"role": "system", "content": system_msg},     # citation rules
            {"role": "user", "content": user_msg}          # query + sources
        ],
        max_tokens=MAX_TOKENS,                              # limit response length
        temperature=0.1                                     # low temperature = factual, consistent
    )

    answer_text = response.choices[0].message.content       # extract the answer text

    print("  ✅ Answer generated with citations\n")          # done message

    return {
        "query": query,                                      # original question
        "answer": answer_text,                               # the cited answer
        "chunks_used": reranked_chunks,                      # which chunks informed the answer
        "refused": False                                     # we did not refuse
    }


# --- QUICK TEST ---
if __name__ == "__main__":
    from hybrid_retriever import hybrid_search               # Step 1 function
    from reranker import rerank_chunks                       # Step 2 function

    test_query = "What is the minimum CET1 capital ratio requirement under Basel III?"

    print("Step 1: Hybrid retrieval...")
    hybrid_chunks = hybrid_search(test_query, top_k=5)      # retrieve 5 chunks

    print("Step 2: Cohere reranking...")
    reranked = rerank_chunks(test_query, hybrid_chunks, top_n=3)  # rerank to top 3

    print("Step 3: Generating cited answer...")
    result = generate_cited_answer(test_query, reranked)    # generate with citations

    print("=" * 60)
    print("CITED ANSWER")
    print("=" * 60)
    print(result["answer"])                                  # print the full answer
    print(f"\nRefused: {result['refused']}")                 # did we refuse?
    print(f"Chunks used: {len(result['chunks_used'])}")      # how many chunks informed answer
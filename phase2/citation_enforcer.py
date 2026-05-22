# =============================================================================
# What this file does:
# Builds a citation-enforced prompt from reranked chunks and sends it to
# the Groq LLM. Now reads ALL prompt config (system prompt, model, temperature,
# thresholds) from phase2/prompts/rag_prompt.yaml instead of hardcoded values.
# Changing prompt behavior = editing the YAML file, not this Python file.
# =============================================================================

import os                            # for reading environment variables
from groq import Groq                # Groq SDK for LLM generation
from dotenv import load_dotenv       # for loading .env file
from prompt_loader import get_system_prompt, get_user_prompt, get_model_config  # YAML loader

load_dotenv()                        # load GROQ_API_KEY from .env

# --- CONFIGURATION — now loaded from YAML, not hardcoded ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")    # still read API key from .env (never put keys in YAML)


def build_source_block(chunks, score_threshold):
    """
    Filters chunks by Cohere score threshold and builds the numbered source block string.
    Returns (source_block_string, filtered_chunks_list).
    """
    filtered_chunks = [                                      # keep only high-quality chunks
        chunk for chunk in chunks
        if chunk.get("cohere_score", 1.0) >= score_threshold
    ]

    if not filtered_chunks:                                  # nothing passed the filter
        return None, []                                      # signal refusal

    source_block = ""                                        # build the numbered source text
    for i, chunk in enumerate(filtered_chunks):
        source_num = i + 1                                   # 1-based numbering
        source = chunk.get("source", "Unknown document")
        page = chunk.get("page", "?")
        if source == "Unknown document" and "metadata" in chunk:
            source = chunk["metadata"].get("source", "Unknown document")
            page = chunk["metadata"].get("page", page)
        text = chunk["text"].strip()
        source_block += f"[{source_num}] Source: {source} | Page: {page}\n"
        source_block += f"{text}\n\n"

    return source_block, filtered_chunks                     # return both


def generate_cited_answer(query, reranked_chunks):
    """
    Full pipeline: loads YAML config → builds cited prompt → sends to Groq → returns answer.
    All prompt text and model settings now come from rag_prompt.yaml.
    """
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not found in .env file")

    print("  → Loading prompt config from YAML...")
    model_config = get_model_config()                        # load model settings from YAML

    print("  → Building citation-enforced prompt...")
    source_block, filtered_chunks = build_source_block(     # build numbered source text
        reranked_chunks,
        model_config["cohere_score_threshold"]               # threshold from YAML
    )

    if source_block is None:                                 # no chunks passed threshold
        return {
            "query": query,
            "answer": "INSUFFICIENT SOURCE MATERIAL: No retrieved chunks met the minimum relevance threshold.",
            "chunks_used": [],
            "refused": True
        }

    system_msg = get_system_prompt()                         # load system prompt from YAML
    user_msg = get_user_prompt(query, source_block)          # fill in user prompt template

    print("  → Sending to Groq LLM for generation...")
    client = Groq(api_key=GROQ_API_KEY)                     # create Groq client

    response = client.chat.completions.create(
        model=model_config["model"],                         # model name from YAML
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ],
        max_tokens=model_config["max_tokens"],               # max tokens from YAML
        temperature=model_config["temperature"]              # temperature from YAML
    )

    answer_text = response.choices[0].message.content
    print("  ✅ Answer generated with citations\n")

    return {
        "query": query,
        "answer": answer_text,
        "chunks_used": filtered_chunks,
        "refused": False,
        "prompt_version": get_model_config().get("prompt_version", "unknown")  # track version
    }


# --- QUICK TEST ---
if __name__ == "__main__":
    from hybrid_retriever import hybrid_search
    from reranker import rerank_chunks

    test_query = "What is the minimum CET1 capital ratio requirement under Basel III?"

    print("Step 1: Hybrid retrieval...")
    hybrid_chunks = hybrid_search(test_query, top_k=5)

    print("Step 2: Cohere reranking...")
    reranked = rerank_chunks(test_query, hybrid_chunks, top_n=3)

    print("Step 3: Generating cited answer from YAML-configured prompt...")
    result = generate_cited_answer(test_query, reranked)

    print("=" * 60)
    print("CITED ANSWER (prompt loaded from YAML)")
    print("=" * 60)
    print(result["answer"])
    print(f"\nRefused: {result['refused']}")
    print(f"Chunks used: {len(result['chunks_used'])}")
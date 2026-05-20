# ==============================================================================
# What this file does:
# This is the Retrieval module for FinReg-RAG.
# It takes a user's natural language question, converts it to a vector
# using the same embedding model we used in Step 3, searches ChromaDB
# for the most semantically similar chunks, and returns them ranked
# by relevance. These chunks become the "context" for Claude in generate.py.
# ==============================================================================

import os                            # Built-in — for file paths
from sentence_transformers import SentenceTransformer  # Same model as Step 3
import chromadb                      # Our vector database


# ==============================================================================
# CONFIGURATION — must match exactly what we used in embed_and_store.py
# ==============================================================================

EMBEDDING_MODEL  = "all-MiniLM-L6-v2"   # Same model used to embed chunks
CHROMADB_PATH    = os.path.join("data", "chromadb")  # Where our DB lives on disk
COLLECTION_NAME  = "finreg_documents"    # Same collection name as Step 3
TOP_K_RESULTS    = 5                     # How many chunks to retrieve per query


def load_retrieval_components() -> tuple:
    """
    Loads the embedding model and ChromaDB collection.
    Returns a tuple of (model, collection) ready for searching.
    We call this ONCE at startup to avoid reloading on every query.
    """

    # Load the embedding model — same one we used to embed chunks
    # Loading from cache this time — no download needed
    print("Loading embedding model for retrieval...")
    model = SentenceTransformer(EMBEDDING_MODEL)

    # Connect to the existing ChromaDB database on disk
    # PersistentClient opens the existing database — does NOT create a new one
    print(f"Connecting to ChromaDB at: {CHROMADB_PATH}")
    client = chromadb.PersistentClient(path=CHROMADB_PATH)

    # Get our existing collection — must already exist from Step 3
    # This will raise an error if the collection doesn't exist yet
    collection = client.get_collection(name=COLLECTION_NAME)

    # Confirm how many vectors are available to search
    print(f"Connected! Collection contains {collection.count()} vectors")

    # Return both components for use in the retrieve function
    return model, collection


def retrieve_relevant_chunks(query: str, model: SentenceTransformer,
                              collection, top_k: int = TOP_K_RESULTS) -> list:
    """
    Takes a natural language question and returns the top_k most
    relevant chunks from ChromaDB.

    query:      the user's question as a plain string
    model:      the loaded SentenceTransformer model
    collection: the ChromaDB collection to search
    top_k:      how many results to return (default 5)

    Returns a list of result dictionaries, each containing:
    - text:        the chunk's text content
    - source:      which PDF it came from
    - page_number: which page it was on
    - distance:    how similar it is (lower = more similar)
    """

    # Step 1: Convert the user's question into a vector
    # This uses the EXACT same model and process as when we embedded chunks
    # So the question vector lives in the same mathematical space as chunk vectors
    query_vector = model.encode(query).tolist()

    # Step 2: Search ChromaDB for the closest chunk vectors
    # query_embeddings takes a list of vectors — we only have one query
    # n_results is how many matches to return
    # include tells ChromaDB what data to return alongside the IDs
    results = collection.query(
        query_embeddings=[query_vector],                       # Our query vector
        n_results=top_k,                                       # Return top 5 matches
        include=["documents", "metadatas", "distances"]        # Return text + metadata + scores
    )

    # Step 3: Package results into clean dictionaries
    # results["documents"][0] is a list because we sent one query
    # If we sent multiple queries, [0] would be the first query's results
    retrieved_chunks = []

    # zip() pairs up matching elements from multiple lists simultaneously
    for doc, meta, dist in zip(
        results["documents"][0],   # List of matched chunk texts
        results["metadatas"][0],   # List of matched metadata dicts
        results["distances"][0]    # List of similarity distances
    ):
        # Build a clean result dictionary for each retrieved chunk
        chunk_result = {
            "text":        doc,                      # The chunk's actual text
            "source":      meta.get("source", ""),   # PDF filename
            "page_number": meta.get("page_number", 0), # Page number
            "chunk_index": meta.get("chunk_index", 0), # Position on page
            "distance":    round(dist, 4),           # Similarity score (4 decimal places)
            "relevance":   round(1 - dist, 4)        # Convert to relevance (higher = better)
        }

        # Add to our results list
        retrieved_chunks.append(chunk_result)

    # Return the list of retrieved chunks sorted by relevance (best first)
    return retrieved_chunks


def format_chunks_for_display(chunks: list) -> str:
    """
    Formats retrieved chunks into a human-readable string for debugging.
    Shows source, page, relevance score, and text preview for each chunk.

    chunks: list of chunk dictionaries from retrieve_relevant_chunks()
    """

    # Build the display string line by line
    lines = []
    lines.append(f"\nRetrieved {len(chunks)} chunks:\n")

    # Loop through each chunk and format its key information
    for i, chunk in enumerate(chunks):
        lines.append(f"{'='*50}")
        lines.append(f"Chunk {i+1}")
        lines.append(f"Source:    {chunk['source']} — Page {chunk['page_number']}")
        lines.append(f"Relevance: {chunk['relevance']} (higher = more relevant)")
        lines.append(f"Preview:   {chunk['text'][:300]}...")
        lines.append("")

    # Join all lines with newline characters and return
    return "\n".join(lines)


# This block runs only when you execute this file directly
# Used for testing retrieval in isolation before connecting to Claude
if __name__ == "__main__":

    print("=" * 60)
    print("FinReg-RAG — Retrieval Test")
    print("=" * 60)

    # Load the model and database
    model, collection = load_retrieval_components()

    # Test with a real Basel III question
    test_query = "What is the minimum CET1 capital ratio requirement?"

    print(f"\nSearching for: '{test_query}'")

    # Retrieve the top 5 relevant chunks
    chunks = retrieve_relevant_chunks(test_query, model, collection)

    # Display the results
    print(format_chunks_for_display(chunks))

    print("✅ Retrieval working correctly!")
# ==============================================================================
# What this file does:
# This is the Generation module for FinReg-RAG.
# It supports TWO providers — Groq (primary) and Google Gemini (secondary).
# Groq runs Meta's Llama 3.3 70B model — free, fast, no daily quota issues.
# Gemini is kept as a backup for when Groq is unavailable.
# The RAG prompt, citation enforcement, and hallucination prevention
# logic is identical regardless of which provider is used.
# Only generate.py changes — everything else in the pipeline is untouched.
# ==============================================================================

import os                       # Built-in — for reading environment variables
from groq import Groq           # Groq's official Python SDK
from dotenv import load_dotenv  # Loads our .env file safely


# ==============================================================================
# LOAD ENVIRONMENT VARIABLES
# ==============================================================================

# Load the .env file so API keys become available as environment variables
load_dotenv()


# ==============================================================================
# CONFIGURATION
# ==============================================================================

# Read the Groq API key from environment — NEVER hardcode secrets in code
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# The model we use via Groq
# llama-3.3-70b-versatile is Groq's best free model — excellent for regulatory Q&A
# It's Meta's Llama 3.3 with 70 billion parameters — genuinely powerful
MODEL_NAME = "llama-3.3-70b-versatile"

# Maximum tokens in the response
# 1024 tokens ≈ 750 words — enough for detailed regulatory answers
MAX_TOKENS = 1024

# Temperature controls randomness in responses
# 0.1 = very focused and precise — what we want for compliance answers
# 1.0 = creative but less accurate — wrong for our use case
TEMPERATURE = 0.1


def initialize_groq() -> Groq:
    """
    Creates and returns a configured Groq client.
    Call this ONCE at startup — reuse the client for all queries.

    Returns a Groq client instance ready to generate content.
    """

    # Verify the API key exists before attempting any API calls
    if not GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY not found!\n"
            "Make sure your .env file contains: GROQ_API_KEY=gsk_your-key-here\n"
            "Get a free key at: https://console.groq.com"
        )

    # Create the Groq client — this is all the initialization needed
    # Groq's SDK is designed to be very similar to OpenAI's SDK
    client = Groq(api_key=GROQ_API_KEY)

    # Confirm initialization
    print(f"Groq client initialized — using model: {MODEL_NAME}")

    # Return the client for reuse
    return client


def build_rag_prompt(question: str, chunks: list) -> str:
    """
    Builds the RAG prompt sent to the LLM.
    This is our core hallucination-prevention mechanism.

    Contains three parts:
    1. Labeled excerpts from retrieved chunks (the grounding context)
    2. Strict rules forcing citation-only answers
    3. The user's question

    question: the user's natural language question
    chunks:   list of retrieved chunk dicts from retrieve.py
    """

    # Build the context block — label each chunk with source + page
    context_parts = []

    # Format each chunk as a clearly labeled excerpt
    for i, chunk in enumerate(chunks):

        # Header shows excerpt number, source file, and page number
        # This is exactly what the LLM will reference when writing citations
        excerpt_header = (
            f"[EXCERPT {i+1}] "
            f"Source: {chunk['source']} | "
            f"Page: {chunk['page_number']}"
        )

        # Combine header with the chunk's text content
        context_parts.append(f"{excerpt_header}\n{chunk['text']}")

    # Join all excerpts with a clear visual separator
    context_block = "\n\n---\n\n".join(context_parts)

    # Build the complete prompt with strict citation enforcement rules
    # Every rule exists specifically to prevent hallucination in financial Q&A
    prompt = f"""You are a financial regulatory compliance assistant specializing
in interpreting official regulatory documents for banking professionals.

You have been provided with excerpts from official financial regulatory documents.
Answer the user's question using ONLY the information in these excerpts.

STRICT RULES — follow without exception:
1. Answer ONLY from the provided excerpts — use NO outside knowledge whatsoever
2. Always cite sources using this exact format: (Source: filename, Page: N)
3. If excerpts lack sufficient information to answer, respond with exactly:
   "I cannot answer this question based on the provided document excerpts."
4. Never guess, infer, or extrapolate beyond what excerpts explicitly state
5. Use precise regulatory language — do not paraphrase in ways that alter meaning
6. If multiple excerpts support the answer, cite all of them
7. Lead with the direct answer first, then provide supporting detail

DOCUMENT EXCERPTS:
{context_block}

USER QUESTION:
{question}

ANSWER (cite every claim with its source and page number):"""

    # Return the complete prompt string
    return prompt


def generate_answer(question: str, chunks: list, client: Groq) -> dict:
    """
    Sends the question + retrieved chunks to Groq/Llama and returns
    a structured response dictionary.

    question: the user's natural language question
    chunks:   list of retrieved chunk dicts from retrieve.py
    client:   the initialized Groq client from initialize_groq()

    Returns a dict containing:
    - answer:        the LLM's cited response text
    - question:      the original question
    - sources_used:  list of sources provided as context
    - model:         which model generated the answer
    - chunks_used:   how many chunks were provided
    - tokens_used:   tokens consumed by this response
    """

    # Build the RAG prompt with our retrieved context
    prompt = build_rag_prompt(question, chunks)

    # Log what we're about to send so the user can follow along
    print(f"Sending query to {MODEL_NAME} via Groq...")
    print(
        f"Context: {len(chunks)} chunks | "
        f"~{sum(len(c['text']) for c in chunks)} characters"
    )

    # Send the request to Groq
    # Groq's API follows the OpenAI chat completions format exactly
    # messages is a list — "system" sets behavior, "user" is the prompt
    completion = client.chat.completions.create(
        model=MODEL_NAME,         # Which model to use
        messages=[
            {
                # System message sets the overall behavior of the model
                "role": "system",
                "content": (
                    "You are a precise financial regulatory compliance assistant. "
                    "You answer questions exclusively from provided document excerpts "
                    "and always cite your sources. You never hallucinate or use "
                    "knowledge outside the provided context."
                )
            },
            {
                # User message contains our full RAG prompt
                "role": "user",
                "content": prompt
            }
        ],
        temperature=TEMPERATURE,  # Low temperature = focused, precise answers
        max_tokens=MAX_TOKENS,    # Cap the response length
    )

    # Extract the generated text from the completion response
    # completion.choices[0].message.content is the standard OpenAI-style access
    answer_text = completion.choices[0].message.content

    # Build a deduplicated list of sources provided as context
    # set() removes duplicates if same page appears in multiple chunks
    sources_used = list(set([
        f"{chunk['source']} (Page {chunk['page_number']})"
        for chunk in chunks
    ]))

    # Extract token usage from the response metadata
    # completion.usage tracks prompt tokens + completion tokens
    tokens_used = 0
    if hasattr(completion, 'usage') and completion.usage:
        # completion_tokens is how many tokens the model generated
        tokens_used = getattr(completion.usage, 'completion_tokens', 0)

    # Package everything into a clean response dictionary
    result = {
        "question":     question,       # Original question
        "answer":       answer_text,    # The cited answer
        "sources_used": sources_used,   # Sources provided as context
        "chunks_used":  len(chunks),    # Number of chunks used
        "model":        MODEL_NAME,     # Model that generated the answer
        "tokens_used":  tokens_used     # Tokens consumed
    }

    # Return the complete result
    return result


def display_response(response: dict) -> None:
    """
    Prints a clean, readable version of the RAG response to the terminal.

    response: the dictionary returned by generate_answer()
    """

    print("\n" + "=" * 60)
    print("  FINREG-RAG RESPONSE")
    print("=" * 60)

    # Print the original question
    print(f"\n📋 QUESTION:\n{response['question']}")

    # Print the cited answer
    print(f"\n📄 ANSWER:\n{response['answer']}")

    # Print sources that were provided as context
    print(f"\n📚 SOURCES PROVIDED AS CONTEXT:")
    for source in response['sources_used']:
        print(f"   • {source}")

    # Print technical metadata
    print(f"\n⚙️  METADATA:")
    print(f"   Model:       {response['model']}")
    print(f"   Provider:    Groq")
    print(f"   Chunks used: {response['chunks_used']}")
    print(f"   Tokens used: {response['tokens_used']}")
    print("=" * 60)


# Runs only when you execute this file directly — used for pipeline testing
if __name__ == "__main__":

    # Import retrieval functions
    from retrieve import load_retrieval_components, retrieve_relevant_chunks

    print("=" * 60)
    print("FinReg-RAG — Full Pipeline Test (Groq + Llama 3.3 70B)")
    print("=" * 60)

    # Step 1: Initialize Groq client
    client = initialize_groq()

    # Step 2: Load retrieval model and ChromaDB
    retrieval_model, collection = load_retrieval_components()

    # Step 3: Define our test question
    question = (
        "What is the minimum CET1 capital ratio and "
        "what happens if a bank falls below it?"
    )
    print(f"\nQuestion: {question}")

    # Step 4: Retrieve relevant chunks
    print("\nRetrieving relevant chunks...")
    chunks = retrieve_relevant_chunks(question, retrieval_model, collection)
    print(f"Retrieved {len(chunks)} chunks")

    # Step 5: Generate cited answer
    response = generate_answer(question, chunks, client)

    # Step 6: Display formatted response
    display_response(response)

    print("\n✅ Full RAG pipeline working end-to-end with Groq!")
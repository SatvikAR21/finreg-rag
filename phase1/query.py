# ==============================================================================
# What this file does:
# Interactive query interface for FinReg-RAG Phase 1.
# Now powered by Groq + Llama 3.3 70B — free, fast, no daily quota limits.
# Loads all components once at startup then loops accepting user questions
# until they type 'quit'.
# ==============================================================================

# Import retrieval functions from retrieve.py
from retrieve import (
    load_retrieval_components,
    retrieve_relevant_chunks,
    format_chunks_for_display
)

# Import generation functions from updated generate.py
from generate import (
    initialize_groq,
    generate_answer,
    display_response
)


def run_interactive_query_loop() -> None:
    """
    Main interactive loop — accepts questions, returns cited answers.
    Runs until the user types 'quit' or 'exit'.
    """

    # Print welcome banner
    print("\n" + "=" * 60)
    print("  FINREG-RAG — Financial Regulatory AI Assistant")
    print("  Phase 1 — Basel III | Powered by Groq + Llama 3.3 70B")
    print("=" * 60)
    print("\nAnswers questions using ONLY the Basel III regulatory")
    print("framework document. Every answer includes citations.")
    print("\nCommands:")
    print("  Any question     → get a cited answer")
    print("  debug <question> → see retrieved chunks before answer")
    print("  quit             → exit the program")
    print("=" * 60)

    # Initialize ALL components ONCE at startup
    # Doing this inside the loop would add seconds to every single query
    print("\nInitializing system components...")

    # Initialize Groq client
    groq_client = initialize_groq()

    # Load sentence-transformer embedding model and ChromaDB collection
    retrieval_model, collection = load_retrieval_components()

    # Everything is ready
    print("\n✅ System ready! Ask your first Basel III question.\n")

    # Main query loop — runs until user quits
    while True:

        # Get user input and strip accidental whitespace
        user_input = input("\n❓ Your question: ").strip()

        # Handle empty input gracefully
        if not user_input:
            print("Please type a question or 'quit' to exit.")
            continue

        # Handle quit commands
        if user_input.lower() in ["quit", "exit", "q"]:
            print("\nThank you for using FinReg-RAG. Goodbye! 👋")
            break

        # Detect debug mode — shows raw retrieved chunks before the answer
        debug_mode = False
        if user_input.lower().startswith("debug "):
            debug_mode = True
            # Remove the "debug " prefix to get the real question
            user_input = user_input[6:].strip()
            print("\n🔍 Debug mode ON — showing retrieved chunks first")

        # Wrap everything in try/except so errors never crash the loop
        try:

            # Step 1: Search ChromaDB for relevant chunks
            print("\n🔎 Searching knowledge base...")
            chunks = retrieve_relevant_chunks(
                user_input,
                retrieval_model,
                collection
            )

            # Show raw chunks in debug mode before generating answer
            if debug_mode:
                print(format_chunks_for_display(chunks))

            # Step 2: Send chunks + question to Groq for generation
            response = generate_answer(user_input, chunks, groq_client)

            # Step 3: Display the formatted cited response
            display_response(response)

        # Handle errors with specific, helpful messages
        except Exception as e:

            error_str = str(e).lower()

            # Rate limit errors
            if "429" in error_str or "rate" in error_str or "quota" in error_str:
                print("\n⚠️  Rate limit reached.")
                print("Groq free tier: 30 requests/minute.")
                print("Wait 60 seconds and try again.")

            # Authentication errors
            elif "401" in error_str or "403" in error_str or "api key" in error_str:
                print("\n❌ API Key Error.")
                print("Check your GROQ_API_KEY in the .env file.")
                print("Get a free key at: https://console.groq.com")

            # Connection errors
            elif "connection" in error_str or "timeout" in error_str:
                print("\n❌ Connection Error.")
                print("Check your internet connection and try again.")

            # All other errors — show the actual message for debugging
            else:
                print(f"\n❌ Unexpected error: {e}")
                print("Type 'quit' to exit or try a different question.")


# Entry point — runs the interactive loop when file is executed directly
if __name__ == "__main__":
    run_interactive_query_loop()
## Phase 1 — Document Ingestion and Embedding

Parses regulatory PDFs using PyMuPDF, splits them into overlapping chunks
using LangChain's RecursiveCharacterTextSplitter, generates embeddings with
sentence-transformers (all-MiniLM-L6-v2), and stores them in a local
ChromaDB vector store. Output: 600+ searchable vectors of Basel III.

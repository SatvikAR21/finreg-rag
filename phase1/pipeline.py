# =============================================================================
# What this file does:
# Provides a single ingest_document() function that runs the complete
# ingestion pipeline on any PDF file:
#   1. Extract text page by page (ingest)
#   2. Split into overlapping chunks (chunk)
#   3. Embed chunks and store in ChromaDB (embed_and_store)
#
# Used by the FastAPI /upload endpoint so the UI can trigger ingestion.
# =============================================================================

import os               # for file path operations
import sys              # for path manipulation

# --- PATH SETUP ---
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _PROJECT_ROOT)

import fitz                                                          # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter  # chunking
import chromadb                                                      # vector database
from sentence_transformers import SentenceTransformer                # embeddings

# --- CONFIGURATION ---
CHROMA_PATH     = os.path.join(_PROJECT_ROOT, "data", "chromadb")
COLLECTION_NAME = "finreg_documents"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHUNK_SIZE      = 500
CHUNK_OVERLAP   = 50
PROCESSED_DIR   = os.path.join(_PROJECT_ROOT, "data", "processed")

# Lazy-loaded embedding model — None until first use
_MODEL = None


def ingest_document(pdf_path: str) -> dict:
    """
    Runs the complete ingestion pipeline on a single PDF file.
    Returns a dict with success, filename, pages, chunks, message.
    """
    global _MODEL                                 # access module-level variable

    filename = os.path.basename(pdf_path)         # e.g. "basel3_framework.pdf"
    doc_id   = filename.replace(".pdf", "")       # e.g. "basel3_framework"

    print(f"\n📄 Starting ingestion: {filename}")

    # ── STAGE 1: EXTRACT TEXT FROM PDF ─────────────────────────
    print("  → Stage 1: Extracting text from PDF...")
    try:
        doc = fitz.open(pdf_path)                 # open the PDF with PyMuPDF
    except Exception as e:
        return {
            "success": False, "filename": filename,
            "pages": 0, "chunks": 0,
            "message": f"Failed to open PDF: {str(e)}"
        }

    pages_data = []
    for page_num in range(len(doc)):              # loop through every page
        page = doc[page_num]
        text = page.get_text()
        if text.strip():                          # skip blank pages
            pages_data.append({
                "source": filename,
                "page":   page_num + 1,
                "text":   text,
            })
    doc.close()

    if not pages_data:
        return {
            "success": False, "filename": filename,
            "pages": 0, "chunks": 0,
            "message": "No text could be extracted. The PDF may be scanned/image-based."
        }

    print(f"     Extracted {len(pages_data)} pages")

    # ── STAGE 2: CHUNK THE EXTRACTED TEXT ──────────────────────
    print("  → Stage 2: Splitting pages into chunks...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " ", ""],
    )

    all_chunks = []
    for page_record in pages_data:
        splits = splitter.split_text(page_record["text"])
        for i, chunk_text in enumerate(splits):
            all_chunks.append({
                "text":      chunk_text,
                "source":    page_record["source"],
                "page":      page_record["page"],
                "chunk_num": i,
            })

    if not all_chunks:
        return {
            "success": False, "filename": filename,
            "pages": len(pages_data), "chunks": 0,
            "message": "Text was extracted but could not be chunked."
        }

    print(f"     Created {len(all_chunks)} chunks")

    # ── STAGE 3: EMBED AND STORE IN CHROMADB ───────────────────
    print("  → Stage 3: Embedding chunks and storing in ChromaDB...")

    # Load model lazily on first upload
    if _MODEL is None:
        print("     Loading embedding model...")
        _MODEL = SentenceTransformer(EMBEDDING_MODEL)   # load only when needed

    client     = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(COLLECTION_NAME)

    ids        = []
    documents  = []
    metadatas  = []
    embeddings = []

    existing_count = collection.count()          # avoid ID collisions

    texts_to_embed = [c["text"] for c in all_chunks]
    vectors = _MODEL.encode(                     # embed all chunks at once
        texts_to_embed,
        show_progress_bar=False                  # disable progress bar in server context
    ).tolist()

    for i, (chunk, vector) in enumerate(zip(all_chunks, vectors)):
        chunk_id = f"{doc_id}_p{chunk['page']}_c{chunk['chunk_num']}_{existing_count + i}"
        ids.append(chunk_id)
        documents.append(chunk["text"])
        metadatas.append({
            "source": chunk["source"],
            "page":   str(chunk["page"])
        })
        embeddings.append(vector)

    # Insert in batches of 100
    batch_size = 100
    for start in range(0, len(ids), batch_size):
        end = start + batch_size
        collection.add(
            ids=ids[start:end],
            documents=documents[start:end],
            metadatas=metadatas[start:end],
            embeddings=embeddings[start:end],
        )
        print(f"     Stored batch {start//batch_size + 1} "
              f"({min(end, len(ids))}/{len(ids)} chunks)")

    print(f"  ✅ Ingestion complete: {len(all_chunks)} chunks stored for {filename}\n")

    return {
        "success":  True,
        "filename": filename,
        "pages":    len(pages_data),
        "chunks":   len(all_chunks),
        "message":  f"Successfully ingested {len(pages_data)} pages "
                    f"and {len(all_chunks)} chunks into ChromaDB."
    }


def get_ingested_documents() -> list:
    """
    Returns all unique documents currently stored in ChromaDB.
    """
    try:
        client     = chromadb.PersistentClient(path=CHROMA_PATH)
        collection = client.get_or_create_collection(COLLECTION_NAME)
        total      = collection.count()

        if total == 0:
            return []

        all_sources = {}
        batch       = 100
        offset      = 0

        while offset < total:
            results = collection.get(
                limit=batch,
                offset=offset,
                include=["metadatas"]
            )
            for meta in results["metadatas"]:
                src = meta.get("source", "unknown")
                all_sources[src] = all_sources.get(src, 0) + 1
            offset += batch

        documents = []
        for source, chunk_count in all_sources.items():
            documents.append({
                "filename": source,
                "chunks":   chunk_count,
                "status":   "ready",
            })

        return documents

    except Exception as e:
        print(f"Error fetching documents: {e}")
        return []
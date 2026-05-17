# ==============================================================================
# What this file does:
# This is the Document Ingestion module for FinReg-RAG.
# It opens PDF files from the data/raw/ folder, extracts all text page by page,
# attaches metadata (source file name, page number) to each page's text,
# and saves everything as a structured JSON file in data/processed/.
# This JSON file is the input for the next step: chunking.
# ==============================================================================

import fitz          # PyMuPDF library — lets us open and read PDF files
import json          # Built-in Python library — lets us save data as JSON files
import os            # Built-in Python library — lets us work with file paths and folders
from datetime import datetime  # Built-in — lets us record when ingestion happened

def extract_text_from_pdf(pdf_path: str) -> list:
    """
    Opens a single PDF file and extracts text from every page.
    Returns a list of dictionaries, one per page.
    
    pdf_path: the full file path to the PDF we want to read
    """
    
    # Print a message so we know the function started
    print(f"Opening PDF: {pdf_path}")
    
    # Open the PDF file using PyMuPDF's open function
    # 'doc' now represents the entire PDF document in memory
    doc = fitz.open(pdf_path)
    
    # Get just the filename from the full path (e.g., "basel3_framework.pdf")
    # os.path.basename strips away the folder path and keeps only the filename
    filename = os.path.basename(pdf_path)
    
    # Create an empty list that will hold one dictionary per page
    pages = []
    
    # Loop through every page in the document
    # len(doc) gives us the total number of pages
    # enumerate gives us both the index (page_num) and the page object itself
    for page_num, page in enumerate(doc):
        
        # Extract all the text from this single page
        # get_text("text") returns plain text, stripping formatting
        text = page.get_text("text")
        
        # Skip pages that have no text (e.g., blank pages or image-only pages)
        # strip() removes whitespace — if nothing is left, the page is empty
        if not text.strip():
            continue  # 'continue' skips to the next page
        
        # Build a dictionary for this page with text + metadata
        # Metadata = information ABOUT the content, not the content itself
        page_data = {
            "source":      filename,           # Which PDF this came from
            "page_number": page_num + 1,       # Page number (humans count from 1, Python from 0)
            "total_pages": len(doc),           # Total pages in the document
            "text":        text.strip(),       # The actual extracted text, whitespace removed
            "ingested_at": datetime.now().isoformat()  # Timestamp of when we processed this
        }
        
        # Add this page's dictionary to our list
        pages.append(page_data)
        
    # Close the PDF file now that we're done reading it
    doc.close()
    
    # Print how many pages we successfully extracted
    print(f"Extracted {len(pages)} pages from {filename}")
    
    # Return the complete list of page dictionaries
    return pages


def save_to_json(pages: list, output_path: str) -> None:
    """
    Saves a list of page dictionaries to a JSON file.
    
    pages: the list of page dictionaries returned by extract_text_from_pdf
    output_path: where to save the JSON file
    """
    
    # Open the output file in write mode ('w')
    # encoding='utf-8' ensures special characters (like € or §) are saved correctly
    with open(output_path, 'w', encoding='utf-8') as f:
        
        # json.dump writes the Python list/dictionary into the file as JSON
        # indent=2 makes the JSON human-readable with nice indentation
        # ensure_ascii=False allows non-English characters to be saved properly
        json.dump(pages, f, indent=2, ensure_ascii=False)
    
    # Confirm the save was successful
    print(f"Saved extracted text to: {output_path}")


def ingest_document(pdf_filename: str) -> str:
    """
    Master function that orchestrates the full ingestion of one PDF.
    Calls extract_text_from_pdf, then save_to_json.
    Returns the path to the saved JSON file.
    
    pdf_filename: just the filename, e.g. "basel3_framework.pdf"
    """
    
    # Build the full path to the input PDF inside data/raw/
    # os.path.join correctly handles folder separators on any OS
    pdf_path = os.path.join("data", "raw", pdf_filename)
    
    # Check that the PDF actually exists before trying to open it
    # This prevents confusing errors later
    if not os.path.exists(pdf_path):
        # Raise an error with a clear message if the file isn't found
        raise FileNotFoundError(f"PDF not found at: {pdf_path}")
    
    # Call our extraction function to get the list of page dictionaries
    pages = extract_text_from_pdf(pdf_path)
    
    # Build the output filename by replacing .pdf with .json
    # e.g., "basel3_framework.pdf" becomes "basel3_framework.json"
    output_filename = pdf_filename.replace(".pdf", ".json")
    
    # Build the full path to where we'll save the JSON in data/processed/
    output_path = os.path.join("data", "processed", output_filename)
    
    # Make sure the data/processed/ folder exists (create it if it doesn't)
    # exist_ok=True means "don't crash if the folder already exists"
    os.makedirs(os.path.join("data", "processed"), exist_ok=True)
    
    # Save the extracted pages to JSON
    save_to_json(pages, output_path)
    
    # Return the output path so the caller knows where the file was saved
    return output_path


# This block runs only when you execute this file directly
# It will NOT run if this file is imported by another file
if __name__ == "__main__":
    
    # Tell the user we're starting
    print("=" * 60)
    print("FinReg-RAG — Document Ingestion")
    print("=" * 60)
    
    # Ingest our first document — Basel III framework PDF
    output = ingest_document("basel3_framework.pdf")
    
    # Print the final success message with the output location
    print(f"\n✅ Ingestion complete! Output saved to: {output}")
    print("You can now open this JSON file to inspect the extracted text.")
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database import get_db_connection
import os

import PyPDF2
from pathlib import Path

# Connect to database
DB_PATH = Path(__file__).parent.parent / "saber11.db"
DOCS_DIR = Path(__file__).parent.parent / "docs"

def get_db():
    return get_db_connection()

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
    return text

def categorize_area(filename, text):
    # Saber 11 Areas
    filename_lower = filename.lower()
    text_lower = text[:5000].lower() # Check first 5000 chars
    
    if "matematica" in filename_lower or "matemáticas" in filename_lower or "matematicas" in text_lower:
        return "Matemáticas"
    if "lectura" in filename_lower or "critica" in filename_lower or "lectura crítica" in text_lower:
        return "Lectura Crítica"
    if "social" in filename_lower or "ciudadana" in filename_lower or "sociales y ciudadanas" in text_lower:
        return "Sociales y Ciudadanas"
    if "natural" in filename_lower or "ciencia" in filename_lower or "ciencias naturales" in text_lower:
        return "Ciencias Naturales"
    if "ingles" in filename_lower or "inglés" in filename_lower or "inglés" in text_lower:
        return "Inglés"
        
    return "General" # Fallback

def ingest_pdfs():
    conn = get_db()
    cursor = conn
    
    print(f"Scanning directory: {DOCS_DIR}")
    for root, dirs, files in os.walk(DOCS_DIR):
        for file in files:
            if file.lower().endswith(".pdf"):
                pdf_path = os.path.join(root, file)
                safe_file = file.encode('ascii', 'ignore').decode('ascii')
                print(f"Processing: {safe_file}...")
                
                text = extract_text_from_pdf(pdf_path)
                if not text:
                    print(f"Warning: No text extracted from {safe_file}")
                    continue
                
                area = categorize_area(file, text)
                
                # Split text into chunks to store in DB (e.g. 2000 chars per chunk to avoid massive rows, or just store the whole text per area if it's small enough. For simplicity, store the whole thing, or maybe chunks of 5000 chars)
                chunk_size = 5000
                chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
                
                for chunk in chunks:
                    cursor.execute(
                        "INSERT INTO knowledge_base (area, content, source_pdf) VALUES (?, ?, ?)",
                        (area, chunk, file)
                    )
                
                print(f"Stored {len(chunks)} chunks for {safe_file} under area {area}.")
    
    conn.commit()
    conn.close()
    print("Ingestion complete.")

if __name__ == "__main__":
    if not DB_PATH.exists():
        print("Database not found. Please run app/database.py first.")
    else:
        ingest_pdfs()

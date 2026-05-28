# David Saber 11

David Saber 11 is a comprehensive, full-stack educational web platform designed to help Colombian students prepare for the Saber 11 exam. It dynamically uses content from official test booklets (`/docs`) to simulate questions and track student progress.

## Features
- **PDF Knowledge Ingestion**: Automatically extracts and categorizes text from Saber 11 PDF booklets.
- **Diagnostic Test**: Initial assessment of the student's level across 5 subjects.
- **Personalized Dashboard**: Visual representation of strengths, weaknesses, and study recommendations.
- **Dynamic Practice Module**: Interactive practice with immediate feedback and contextual explanations.
- **Authentication**: Secure local user registration and login.
- **Premium UI**: Modern, responsive, and student-friendly design using Vanilla CSS.

## Architecture
- **Backend**: Python 3.13 + FastAPI
- **Database**: PostgreSQL (via `psycopg2`)
- **Frontend**: Jinja2 Templates + HTML5 + CSS3 + Vanilla JavaScript
- **PDF Extraction**: PyPDF2
- **AI Integration**: Google Generative AI (Gemini)

### Database Schema
1. **users**: id, email, password_hash, name, streak, badges
2. **diagnostic_results**: user_id, scores for all 5 areas
3. **knowledge_base**: area, text content extracted from PDFs, source_pdf
4. **practice_sessions**: tracking of quiz scores by area and difficulty
5. **questions**: generated AI questions
6. **tutor_chats**: AI tutor chat logs
7. **tutor_duels**: competitive student vs student questions

## Setup Instructions

1. **Clone or Open the Repository**
2. **Set up the Virtual Environment**:
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```
3. **Install Dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```
4. **Environment Variables**:
   Copy `.env.example` to `.env` and fill in your keys (including `GEMINI_API_KEY` and `DATABASE_URL`).
5. **Initialize Database**:
   Ensure you have PostgreSQL running and the `DATABASE_URL` matches your local DB.
   ```powershell
   python app/database.py
   ```
6. **Ingest PDF Knowledge Base**:
   Ensure your Saber 11 PDFs are in the `/docs` folder, then run:
   ```powershell
   python scripts/ingest.py
   ```
7. **Run the Application**:
   ```powershell
   python app/main.py
   ```
   *The server will start at `http://127.0.0.1:8000`*

## Development Plan & Milestones
See `PROJECT_PLAN.md` for details on the MVP roadmap and future enhancements.

## Known Limitations & Future Improvements
- **Question Generation**: Currently, dynamic questions use a mocked heuristic generation that pulls text contexts directly from the `knowledge_base` and presents generic options. *Future Improvement*: Integrate an LLM API (like OpenAI or Gemini) to generate high-quality, semantically accurate multiple-choice questions from the PDF text.
- **Auth System**: The MVP uses simple cookie-based sessions suitable for local demonstration. *Future Improvement*: Implement JWT and standard secure authentication flows (e.g., OAuth).
- **PDF Parsing**: Some old scanned PDFs (e.g., 2024 booklets without OCR text layers) cannot have text extracted via `PyPDF2`. *Future Improvement*: Implement an OCR library like `pytesseract` for image-based PDFs.

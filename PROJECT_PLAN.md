# Project Plan: David Saber 11

## Overview
A web-based educational platform designed to help Colombian students prepare for the Saber 11 exam through dynamic practice questions generated from an internal repository of past exam booklets.

## MVP Definition
The Minimum Viable Product (MVP) will include:
1. **Landing Page**: Explains the platform, areas covered, and benefits.
2. **Authentication**: Basic student registration and login.
3. **PDF Ingestion System**: Backend script to parse PDF files in `/docs` and extract text.
4. **Diagnostic Test**: A quick initial test across 5 subjects to establish a baseline.
5. **Dashboard**: Shows progress, weak areas, and personalized study recommendations.
6. **Practice Module**: Allows practicing dynamically generated questions by subject and difficulty.

## Technology Stack
- **Backend**: Python 3, FastAPI, SQLite, PyMuPDF/PyPDF2 (for PDF extraction).
- **Frontend**: HTML5, Vanilla JS, CSS3 (Rich, Premium Aesthetics).
- **Authentication**: JWT-based or Session-based login.

## Milestones & Phases

### Phase 1: Foundation & Setup
- [x] Create project structure and repository setup.
- [x] Initialize Python virtual environment.
- [x] Set up FastAPI application and SQLite database schema.

### Phase 2: Knowledge Ingestion
- [x] Implement PDF text extraction script.
- [x] Parse `/docs` directory.
- [x] Categorize content by area (Lectura Crítica, Matemáticas, Sociales y Ciudadanas, Ciencias Naturales, Inglés).
- [x] Store knowledge chunks in the database.

### Phase 3: Core Backend Features
- [x] Build Authentication endpoints.
- [x] Create mock Question Generator logic (heuristics using extracted text).
- [x] Implement APIs for the Diagnostic Test and Practice sessions.

### Phase 4: Frontend Development
- [x] Build the Landing Page with modern, responsive CSS.
- [x] Build Auth UI (Login/Register).
- [x] Build the Diagnostic Test view.
- [x] Build the Student Dashboard (progress visualization).
- [x] Build the Practice Module (immediate feedback, explanations).

### Phase 5: Polish & Documentation
- [ ] Apply final UI/UX polish (micro-animations, rich styling).
- [ ] Write `README.md` with setup instructions and architecture decisions.
- [ ] Test the full user flow manually.

## Priorities
1. **PDF Ingestion**: Foundational for the dynamic content.
2. **Backend Architecture**: Reliable database and API.
3. **UI/UX**: Needs to be highly appealing to students (premium feel).

## Future Improvements (Post-MVP)
- Integration with external LLM APIs (OpenAI/Gemini) for high-quality semantic question generation.
- Spaced repetition algorithms for studying.
- Social features (leaderboards, study groups).
- Admin panel to upload new PDFs directly.

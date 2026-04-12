# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

### Setup
- **Python**: Version 3.13 or higher required (specified in `.python-version`)
1. **Install uv** (Python package manager):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
2. **Install Python dependencies**:
   ```bash
   uv sync
   ```
3. **Set up environment variables**:
   - Copy `.env.example` to `.env` in the root directory
   - Add your Anthropic API key: `ANTHROPIC_API_KEY=your_key_here`

### Running the Application
- **Quick start**: Use the provided shell script:
  ```bash
  chmod +x run.sh
  ./run.sh
  ```
- **Manual start**:
  ```bash
  cd backend
  uv run uvicorn app:app --reload --port 8000
  ```
- The application will be available at:
  - Web Interface: `http://localhost:8000`
  - API Documentation: `http://localhost:8000/docs`

### Adding Course Documents
Place course documents (`.txt`, `.pdf`, `.docx`) in the `docs/` directory. The system automatically loads documents on startup. Document format should follow:
- Line 1: `Course Title: [title]`
- Line 2: `Course Link: [url]` (optional)
- Line 3: `Course Instructor: [instructor]` (optional)
- Following lines: Lesson markers (`Lesson X: [title]`) and content

## Architecture Overview

This is a full-stack Retrieval-Augmented Generation (RAG) system for querying course materials. The backend is a FastAPI server that orchestrates document processing, vector search, and AI generation. The frontend is a static HTML/JS interface.

### Key Components

**Backend (`backend/`)**:
- `app.py`: FastAPI application with endpoints `/api/query` and `/api/courses`
- `rag_system.py`: Main orchestrator connecting all components
- `document_processor.py`: Processes course documents into structured `Course` and `CourseChunk` objects
- `vector_store.py`: Manages ChromaDB vector storage with two collections: `course_catalog` (metadata) and `course_content` (chunks)
- `ai_generator.py`: Interfaces with Anthropic's Claude API, includes tool calling for search
- `search_tools.py`: Tool definitions for semantic search with course name matching
- `session_manager.py`: Manages conversation history per session
- `config.py`: Configuration settings loaded from environment variables
- `models.py`: Pydantic models for `Course`, `Lesson`, `CourseChunk`

**Frontend (`frontend/`)**:
- `index.html`: Static interface with sidebar for course stats and suggested questions
- `script.js`: Handles API communication and chat UI
- `style.css`: Styling

**Data**:
- `docs/`: Contains course documents in text format
- `chroma_db/`: Persisted vector database (created automatically)

### Data Flow
1. **Document ingestion**: On startup, documents in `docs/` are processed into chunks and stored in ChromaDB.
2. **Query handling**: User query → FastAPI endpoint → RAGSystem → AI generator with search tool → Vector store search → AI synthesizes results → Response with sources.
3. **Session management**: Each conversation gets a session ID, history is kept for context (limited by `MAX_HISTORY`).

### Configuration
Key settings in `config.py`:
- `CHUNK_SIZE` and `CHUNK_OVERLAP`: Control document chunking
- `MAX_RESULTS`: Number of search results returned
- `MAX_HISTORY`: Conversation history length
- `EMBEDDING_MODEL`: Sentence transformer model for embeddings
- `ANTHROPIC_MODEL`: Claude model variant

## Development Notes

- **Dependencies**: Managed by `uv` with `pyproject.toml` and `uv.lock`
- **No test suite**: Currently no automated tests
- **Windows compatibility**: Use Git Bash for running shell commands
- **API key required**: Anthropic API key must be set in `.env` for AI generation
- **Vector storage**: ChromaDB persists in `chroma_db/` directory; delete this folder to reset knowledge base
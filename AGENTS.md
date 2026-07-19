# Clipt — web article extraction & clipping tool

Extracts main-article content from web pages and exports HTML/DOCX/PDF/Markdown. **Python backend** (`backend/`, deps in `backend/requirements.txt`) + frontend. Optional AI boundary detection via Firecrawl/OpenAI.

## Commands
- Backend deps: `pip install -r backend/requirements.txt` (use a venv)
- Core modules: `clipping_logic.py` (orchestration), `content_extraction.py`, `clean_content.py`, `dom_utils.py`; config in `config.py`/`constants.py`
- Docs: `backend/DOCUMENTATION.md`, top-level `README.md`

## Notes
- REST API mode exists — see README "REST API" section before changing handler signatures

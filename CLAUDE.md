# Claude Code Handoff

## Project Overview
This is a FastAPI + React app for CSV data analytics and agentic dataset exploration.
The backend analyzes uploaded datasets with Pandas, stores cached reports in PostgreSQL, and uses a LangGraph-powered agent workflow for chat-driven analysis.
The frontend is a Vite React dashboard that uploads CSVs, displays summaries and charts, and sends chat queries to the backend.

## Key Architecture
- `app/main.py` — FastAPI application entry point
- `app/api/routes.py` — backend routes for upload, chat, cached dataset lookup, visualization, and PDF generation
- `app/services/data_analyzer.py` — CSV analysis logic and dataset statistics
- `app/agents/workflow.py` — LangGraph agent workflow and tool orchestration
- `app/agents/state.py` — agent state structure for messages, dataset context, tool history, and current file path
- `app/agents/tools.py` — tool functions for summarization, chart generation, anomaly detection, and reporting
- `app/database/connection.py` — SQLAlchemy connection and dependency injection
- `app/models/dataset.py` — persisted dataset report schema

## Current Status
- Backend can upload CSV files and compute a full dataset analysis
- Results are cached in PostgreSQL for repeated uploads
- Chat endpoint initializes an agent state and invokes the LangGraph workflow
- Workflow now captures validated tool output into `tool_history`
- Frontend exists under `frontend/` but should be verified for current endpoint contract

## Important Files and Directories
- `docker-compose.yml` — PostgreSQL service for local development
- `requirements.txt` — Python dependencies
- `frontend/package.json` — frontend JavaScript dependencies
- `data/` — example CSV datasets used for testing and demo
- `tests/test_workflow.py` — regression test for tool result capture

## How to Run Locally
1. Start the database:
   - `docker-compose up -d`
2. Install backend dependencies:
   - `pip install -r requirements.txt`
3. Run the backend:
   - `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
4. Run the frontend from `frontend/`:
   - `npm install`
   - `npm run dev`
5. Open `http://localhost:5173` for the React dashboard and `http://localhost:8000/docs` for API docs

## Verification and Testing
- Backend test command: `pytest tests`
- Check database connectivity by uploading a CSV via `/api/upload`
- Verify the chat flow with `/api/chat`
- Confirm caching with `/api/dataset/cache?filename=<name>`

## Handoff Notes for Claude Code
- The agent loop is in `app/agents/workflow.py`; it receives user messages, runs tool calls, captures tool outputs, and continues reasoning.
- The chat endpoint builds the initial state here:
  - `messages` = user query
  - `current_file_path` = CSV path to analyze
  - `dataset_summary` = any precomputed summary data
  - `tool_history` = list of prior tool outputs
- The current weakest area is multi-step loop control: the agent can capture results, but it still needs better stop/continue decision logic.

## Recommended First Task for Claude Code
1. Read `CLAUDE.md`, the empty `README.md`, and `app/api/routes.py`
2. Confirm the backend API contract and whether the frontend is aligned
3. Improve the agent loop so it can decide when to stop vs. call another tool
4. Add clearer structured responses from the chat endpoint back to the UI

## Notes
- Keep the repo committed and clean before switching tools.
- If you need a stronger handoff, also populate `README.md` with an overview and run instructions.

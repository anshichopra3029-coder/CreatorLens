# CreatorLens project documentation

The specification files in this folder describe the planned product, including later phases. The Phase 1 application now lives in the parent workspace: a React frontend in `frontend/` and a FastAPI backend in `backend/`.

Phase 1 serves labelled demo analytics and validates uploaded CSVs without saving them. Clerk, PostgreSQL, and a trained model are not implemented.

Setup and run commands are in the workspace [README](../README.md). The same PowerShell commands are repeated below.

## Files

- `PRD.md` — product problem, solution, goals, user journey, functional requirements, success criteria, risks, and phases.
- `TRD.md` — technology stack, repository layout, API contracts, data pipeline, optional ML requirements, Clerk/PostgreSQL plan, security, testing, and local development.
- `agent.md` — working instructions for Cursor or another coding agent.
- `architecture.md` — component diagrams, sequence diagrams, logical database model, boundaries, data flow, and architecture decisions.
- `README.md` — this index and the local run commands.

## Run the apps

Backend, from `backend`:

```powershell
cd C:\Users\anshi\OneDrive\Desktop\CretorLens\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

If activation is blocked:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Without activation:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
.\.venv\Scripts\python.exe -m pytest
```

Frontend, from `frontend` in a second window:

```powershell
cd C:\Users\anshi\OneDrive\Desktop\CretorLens\frontend
Copy-Item .env.example .env
npm install
npm run dev
```

The frontend runs at `http://localhost:5173`. The API runs at `http://localhost:8000`. API docs are at `http://localhost:8000/docs`.

## Intended build sequence

1. Foundation: React + TypeScript + Vite frontend and FastAPI backend; mock dashboard data is allowed if clearly labelled; implement real CSV validation. This step is what the current code does.
2. Data science: preprocessing, EDA, metrics, visualizations, computed insights, and tests. Implement ML only if the dataset supports it.
3. Auth/persistence: Clerk authentication, backend identity verification, PostgreSQL, migrations, and user-level data isolation.
4. Polish: tests, documentation, responsive checks, and demo readiness.

## Important product rule

Never show demo data or illustrative insights as if they were generated from a real uploaded dataset. Never claim a machine-learning model or Clerk/database integration works before it has been configured and tested.

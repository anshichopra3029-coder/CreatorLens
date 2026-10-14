# CreatorLens — Agent Instructions

These instructions apply to Cursor and any coding agent working in this repository. Follow them before making code changes.

## 1. Product Context

CreatorLens is a data-science web app for analyzing social media post performance from CSV datasets. It aims to help creators understand historical engagement by cleaning data, calculating valid metrics, visualizing trends, comparing available content categories, and presenting evidence-based insights. A machine-learning feature is optional and may only be enabled after a suitable dataset and evaluation process exist.

Read `PRD.md`, `TRD.md`, and `architecture.md` before implementing a significant feature. If these documents conflict with the actual repository, inspect the code, explain the mismatch, and prefer preserving verified working behavior over blindly rewriting files. Update the documents after an accepted architectural change.

## 2. Intended Architecture

- Frontend: React, TypeScript, Vite, Tailwind CSS, React Router, Recharts, Lucide React.
- Backend: Python, FastAPI, Pydantic, Uvicorn.
- Data science: Pandas, NumPy, and optionally Scikit-learn/Joblib.
- Later phase: Clerk authentication and PostgreSQL persistence, preferably via SQLAlchemy and Alembic.
- Frontend and backend remain logically separate and communicate through documented HTTP APIs.

Do not introduce another framework, database, auth provider, or major dependency without a clear reason and an explicit explanation.

## 3. Phase Boundaries

Implement in this order unless the user explicitly changes priorities:

1. **Foundation:** working frontend routes/layouts, responsive styling, FastAPI skeleton, CORS, typed API client, initial endpoints, truthful CSV upload validation, README and `.env.example` files. Use clearly labelled mock data for dashboard visuals if needed.
2. **Data science:** actual CSV profiling, cleaning, supported metrics, EDA aggregations, charts driven by real API results, traceable insights and tests.
3. **Authentication and persistence:** Clerk sign-in/out, server-side identity verification, PostgreSQL schema/migrations and user-owned data isolation.
4. **Polish:** accessibility, error/empty/loading states, documentation, tests and demo preparation.

Do not add Clerk or PostgreSQL during Phase 1 just because the eventual architecture includes them. Do not start machine-learning work before inspecting the data and defining the prediction target.

## 4. Required Working Method

1. Inspect the current directory, package files, routes, API clients, backend modules, tests, and existing changes before editing.
2. Summarize the relevant current state and the small implementation plan.
3. Implement a coherent, limited slice at a time. Avoid replacing large files or rewriting the project without need.
4. Reuse existing conventions and components. Avoid duplicate helpers, repeated API code, and unnecessary dependencies.
5. Run the relevant type checks, build, tests, or health check after changes when tools are available.
6. Fix errors introduced by the changes; do not claim tests passed if they were not run.
7. Report files changed, commands run, results, remaining issues, and any manual configuration required.

If a command fails because a dependency, credential, or external service is unavailable, state the actual blocker and continue with work that can safely be completed without it. Do not invent successful output.

## 5. Data and Analytics Rules

- Treat all uploaded files and their contents as untrusted input.
- Validate CSV size, format, parsing, row/column structure, and data types.
- Keep original/raw data separate from processed data when it is retained.
- Do not assume that every dataset contains `views`, `reach`, `impressions`, `likes`, `comments`, `shares`, `platform`, `content_type`, or a timestamp. Inspect columns and enable only analyses they support.
- Distinguish missing values from zero values; report cleaning decisions.
- Do not silently drop large amounts of data or fill missing values without a reason.
- Handle zero denominators and return JSON-safe values rather than NaN or Infinity.
- Centralize formulas so the UI and backend do not calculate conflicting versions of the same metric.
- Label the engagement-rate formula and denominator. Do not compare different definitions without explanation.
- Derive insights from actual computed statistics. Include context/sample sizes where appropriate.
- Correlation is not causation. Do not write causal claims from observational data alone.
- Demo fixtures and illustrative insights must be labelled as demo content in code and UI.

## 6. Machine-Learning Rules

Machine learning is optional, not a required decoration. Before adding it:

- Confirm the dataset supports a defensible target and has enough useful examples.
- Define when the prediction is supposed to be made.
- Prevent target leakage by excluding post-outcome variables from a pre-publication prediction.
- Compare to a simple baseline and use suitable evaluation metrics.
- Fit preprocessing only on training data, preferably inside a Scikit-learn Pipeline.
- Use a time-aware split if chronology matters.
- Report limitations and do not display fabricated, unvalidated predictions.
- Never load a model file uploaded by an untrusted user.

If these conditions cannot be met, finish the EDA and leave the prediction feature clearly marked as unavailable or experimental.

## 7. Frontend Conventions

- Use TypeScript and define types for API payloads.
- Keep the API base URL configurable via `VITE_API_BASE_URL`.
- Put API calls in the shared service layer rather than duplicating `fetch` calls across page components.
- Build reusable components for repeated layout and chart behavior.
- Provide loading, error, empty, and success states when meaningful.
- Make buttons and links perform their stated actions. Avoid inert controls.
- Use responsive, accessible layout, labels, keyboard-friendly controls, and readable chart legends.
- Keep the visual style polished and restrained: neutral backgrounds, clear typography, and a limited accent color palette. Avoid excessive gradients, shadows, decorative animation, or clutter.
- Remember that `VITE_*` environment variables are exposed to the client; never put secret values there.

## 8. Backend Conventions

- Keep route handlers thin; implement data logic in service modules.
- Use Pydantic schemas for request/response validation where useful.
- Use consistent status codes and safe, actionable error messages.
- Configure explicit local frontend CORS origins; avoid permissive production CORS.
- Do not expose stack traces, filesystem paths, tokens, or secrets in API responses.
- Do not trust client-provided user IDs for authorization.
- Do not accept a filename as a trusted filesystem path.
- Keep mock data in a dedicated module and replace it deliberately when real analysis is integrated.
- Do not invent database reads/writes in phases where no database exists.

## 9. Clerk and PostgreSQL Rules (Only in the Auth/Persistence Phase)

- Follow current official Clerk guidance for React + Vite and backend token verification; do not rely on a frontend-only route guard for security.
- Verify identity in FastAPI before serving protected resources.
- Determine the authenticated Clerk user ID from the verified token, not a request field.
- Scope every dataset, analysis, and file operation to the authenticated owner.
- Add migrations and indexes for persistent schema changes; do not make undocumented manual schema edits.
- Test that one user cannot read, modify, analyze, or delete another user's data by changing record IDs.
- Keep credentials in ignored environment files or the deployment secret store.
- Store dataset metadata in PostgreSQL. Use controlled file storage for raw CSVs rather than storing large file bodies in relational rows by default.
- Never create fake credentials or claim external integration works before real configuration and tests.

## 10. Repository Hygiene and Documentation

- Keep `.env`, credentials, real/private CSV datasets, uploaded files, virtual environments, `node_modules`, build outputs, and local database files out of Git.
- Maintain a useful `.env.example` with placeholders only.
- Update `README.md` with install, run, test, and configuration steps after changes affecting setup.
- Update `TRD.md` and `architecture.md` when the real technical design changes.
- Add or update tests for non-trivial data logic and security-sensitive behavior.
- Prefer simple, readable code over premature abstraction.

## 11. Definition of Done for Agent Changes

Before calling a task complete, report:

- What was implemented and which files changed.
- Which commands/checks/tests were actually run and their outcomes.
- Whether mock/demo data is still being used anywhere.
- Any required environment variables or manual setup steps.
- Any known limitations or remaining tasks.

Do not say that a feature, test, deployment, Clerk connection, database, or ML model works unless it has been verified in the current workspace.

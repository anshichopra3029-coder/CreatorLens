# CreatorLens — Technical Requirements Document (TRD)

**Document status:** Technical baseline / planned scope  
**Version:** 1.0  
**Last updated:** 14 October 2026

> This document specifies the intended implementation. It is not proof that any phase has already been completed. The implementation should be updated to match the actual repository as work progresses.

## 1. Technical Overview

CreatorLens uses a separate frontend and backend. React renders the user interface; FastAPI exposes HTTP endpoints and owns validation and data-processing orchestration. Pandas and NumPy handle tabular data. Recharts visualizes results. Scikit-learn is introduced only if a suitable prediction target and dataset are available. Clerk and PostgreSQL are a later integration phase.

### Proposed stack

| Layer | Technology | Responsibility |
|---|---|---|
| UI | React + TypeScript + Vite | Client-side application and route layouts |
| Styling | Tailwind CSS | Responsive design and consistent UI tokens |
| Navigation | React Router | Client-side page routing |
| Charts | Recharts | Interactive charts from API responses |
| Icons | Lucide React | Consistent interface icons |
| API | Python + FastAPI | Request validation, endpoints, orchestration |
| API schema | Pydantic | Request/response validation and OpenAPI schema |
| ASGI server | Uvicorn | Local/runtime server for FastAPI |
| Data processing | Pandas + NumPy | CSV profiling, cleaning, aggregations, features |
| Visualization (analysis) | Matplotlib / Seaborn (optional) | EDA in notebooks; dashboard uses Recharts |
| ML (conditional) | Scikit-learn + Joblib | Training, evaluation, and model serialization |
| Authentication (Phase 3) | Clerk | Sign-in, sign-up, identity/session management |
| Relational storage (Phase 3) | PostgreSQL | User-linked metadata and analysis records |
| DB access (Phase 3) | SQLAlchemy 2.x + Alembic | Database models, queries, and migrations |
| Version control | Git + GitHub | Collaborative development and history |

Pin or constrain dependency versions once a working dependency set has been tested. Do not silently upgrade major versions during feature work.

## 2. Logical Architecture

```mermaid
flowchart TD
    U[Creator / Project Evaluator] --> FE[React + TypeScript + Vite]
    FE -->|HTTPS/JSON| API[FastAPI]
    FE -->|Charts| CH[Recharts]
    API --> VAL[Validation and CSV ingestion]
    VAL --> DS[Pandas / NumPy data pipeline]
    DS --> AGG[Metrics, EDA aggregations, insights]
    AGG --> API
    DS -. optional .-> ML[Scikit-learn training/evaluation]
    ML -. validated model only .-> API
    API -. Phase 3 .-> AUTH[Clerk token verification]
    API -. Phase 3 .-> DB[(PostgreSQL)]
    API -. local/dev file storage .-> FS[Configured upload storage]
```

In Phase 1, the dashboard may consume clearly marked mock responses. In Phase 2, analysis endpoints should use actual validated dataset content. In Phase 3, Clerk and PostgreSQL are introduced. No component should claim that a later-phase dependency is active until it has been configured and tested.

## 3. Repository Layout

Recommended layout (adapt only when the current repository gives a good reason):

```text
CreatorLens/
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/       # Reusable UI components
│   │   ├── layouts/          # App shell, sidebar, top bar
│   │   ├── pages/            # Route-level pages
│   │   ├── services/          # Typed API client and endpoints
│   │   ├── types/             # TypeScript API/data types
│   │   ├── data/              # Demo fixtures only, labelled as demo
│   │   ├── hooks/             # Reusable hooks when needed
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── .env.example
│   └── package.json
├── backend/
│   ├── app/
│   │   ├── api/               # Routers/endpoints
│   │   ├── core/              # Settings, CORS, shared config
│   │   ├── schemas/           # Pydantic DTOs
│   │   ├── services/          # Data and analytics business logic
│   │   ├── data/              # Demo fixtures or data helpers
│   │   ├── models/            # SQLAlchemy models, Phase 3
│   │   ├── db/                # Session and migration integration, Phase 3
│   │   └── main.py
│   ├── tests/
│   ├── uploads/               # Local development only; gitignored
│   ├── requirements.txt
│   └── .env.example
├── notebooks/
│   └── 01_eda.ipynb
├── data/
│   ├── raw/                   # Local input data; normally gitignored
│   └── processed/             # Reproducible derived data; normally gitignored
├── models/                    # Trained model artifacts, if used
├── PRD.md
├── TRD.md
├── agent.md
├── architecture.md
├── README.md
└── .gitignore
```

Avoid committing private datasets, uploaded files, `.env` files, credentials, or model artifacts that are not intended to be public.

## 4. Frontend Requirements

### Routes

| Route | Page purpose | Initial state |
|---|---|---|
| `/` | Landing page | Real static product copy; links work |
| `/dashboard` | Overview and KPIs | Clearly labelled demo results until data is loaded |
| `/upload` | Upload CSV and view validation/preview | Real upload interaction in Phase 1 |
| `/analytics` | Compare metrics and trends | Demo data in Phase 1; API-driven in Phase 2 |
| `/insights` | Explain patterns found in data | Demo-labelled examples in Phase 1; computed insights in Phase 2 |
| `/predictions` | Model status and eventual inference form | Explicitly unavailable until a validated model is present |
| `/settings` | Future preferences/profile | Placeholder until persistence/auth exists |

### Frontend implementation rules

- Use TypeScript for API response types and component props.
- Keep the API base URL in `VITE_API_BASE_URL` (example: `http://localhost:8000`).
- Keep HTTP logic in a reusable service module; do not embed fetch logic in every page.
- Add loading, error, and empty states to all API-driven views.
- Use semantic HTML and accessible labels; controls must have meaningful actions.
- Never present mock fixtures as real results. Add a `data_source` or equivalent marker where useful.
- Render filters based on available dimensions rather than assuming every CSV contains the same schema.
- Do not put secrets in frontend environment variables. Variables prefixed with `VITE_` are exposed to the browser.

## 5. Backend Requirements

### API conventions

- Prefix application endpoints with `/api`.
- Use JSON for normal responses and `multipart/form-data` for file uploads.
- Define response shapes with Pydantic models wherever useful.
- Return clear HTTP status codes and user-safe error messages.
- Keep routes thin; put parsing and analytics in services.
- Configure CORS for the known local frontend origin(s), not a broad wildcard in an authenticated production deployment.

### Initial endpoints

| Method | Path | Phase | Purpose |
|---|---|---|---|
| `GET` | `/api/health` | 1 | Health/status response |
| `GET` | `/api/dashboard/summary` | 1 → 2 | Dashboard KPI response; mock first, computed later |
| `GET` | `/api/dashboard/trends` | 1 → 2 | Time-series aggregation for charts |
| `GET` | `/api/dashboard/content-comparison` | 1 → 2 | Category/platform comparison where supported |
| `GET` | `/api/posts` | 1 → 2 | Paginated or bounded recent-post records |
| `POST` | `/api/upload` | 1 → 2 | Validate and profile CSV file |
| `GET` | `/api/datasets/{dataset_id}/profile` | 2 | Schema, row count, null summary, type summary |
| `GET` | `/api/datasets/{dataset_id}/analytics` | 2 | Computed metrics/aggregations for a dataset |
| `GET` | `/api/datasets/{dataset_id}/insights` | 2 | Insights derived from computed statistics |
| `POST` | `/api/datasets/{dataset_id}/predictions` | Conditional | Inference only when a tested model and valid input exist |

In Phase 1, dashboard endpoints may return fixtures from one isolated mock-data module. The upload endpoint must still validate the real uploaded file and return truthful metadata. Do not return a success response if parsing failed.

### Example response shapes

Health:

```json
{"status": "ok", "service": "creatorlens-api"}
```

CSV upload metadata (illustrative contract; adapt as implementation settles):

```json
{
  "filename": "posts.csv",
  "row_count": 120,
  "column_names": ["post_id", "likes", "comments"],
  "data_source": "uploaded_csv",
  "warnings": []
}
```

Do not include the actual file's contents in an upload response. Avoid leaking server paths or stack traces.

## 6. CSV Ingestion and Data Processing

### Input validation

- Accept `.csv` files only for the first release.
- Set a configurable maximum upload size.
- Do not rely on the extension alone; handle parsing errors and unexpected content.
- Bound the number of rows/columns or enforce a size cap to reduce accidental resource exhaustion.
- Use generated server-side identifiers for stored files; do not use an uploaded filename as a storage path.
- Report duplicate, missing, malformed, and unsupported columns without silently inventing values.
- Treat uploaded CSV data as untrusted input; never execute values as code or formulas.

### Suggested processing stages

1. Parse and profile the original file.
2. Normalize column names for internal use while retaining a mapping to original names.
3. Infer and validate data types.
4. Parse dates with explicit failure counts.
5. Detect duplicate rows and possible repeated post snapshots.
6. Validate numeric fields and identify impossible values.
7. Apply documented handling for missing values.
8. Build derived fields only when their source fields are present.
9. Compute summary statistics and group aggregations.
10. Return metrics, data-quality warnings, and enough metadata for the UI to explain the result.

Do not mutate the only copy of the raw source. For reproducibility, preserve the source or its controlled reference separately from processed representations.

## 7. Metrics and Analytics Logic

- Metrics must be defined centrally in the backend, not recalculated inconsistently in multiple pages.
- Use medians as well as means when distributions are strongly skewed.
- Filter choices must use actual distinct values and avoid assuming platform or content-type columns exist.
- Time-based views require a parseable timestamp/date field.
- Handle zero denominators and empty groups without NaN or infinity leaking into JSON.
- Include sample size alongside group comparisons where useful.
- Document whether an average is per post, per creator, or weighted by reach/views.
- Any insight-generation rule must be deterministic and traceable to the computed data.

### Engagement rate

One optional formula is:

`view_based_engagement_rate = (likes + comments + shares) / views * 100`

It requires all relevant component columns and a valid `views` denominator. If shares or views are absent, do not silently substitute another field. If an alternate formula is used, give it a distinct name and document it.

## 8. Machine Learning Requirements (Conditional Phase)

Machine learning is not required merely to call the project data science. EDA and defensible analytics are required first. Add a model only after dataset suitability is confirmed.

- Explicitly define the target (for example, an engagement measure or a performance class).
- Decide whether the task is regression or classification based on that target.
- Use a simple baseline before evaluating a more complex model.
- Split data before fitting preprocessing operations; fit scalers/encoders using training data only, preferably through an sklearn Pipeline.
- Use time-aware splitting where chronological leakage is likely.
- Keep post-outcome information (such as final engagement totals) out of features for a prediction supposedly made before publishing.
- Select appropriate metrics: MAE/RMSE for regression; precision, recall, F1 and/or ROC-AUC where appropriate for classification and class distribution.
- Compare the model against a baseline and document uncertainty and limitations.
- Do not expose predictions if the model artifact is missing, incompatible, or has failed validation.
- Treat serialized model files as trusted build artifacts; never load untrusted pickle/joblib files supplied by end users.

## 9. Clerk and PostgreSQL Integration (Phase 3)

### Authentication

- Use Clerk for identity and session management on the React client.
- The frontend attaches a valid Clerk session token to protected API requests using the supported Clerk SDK flow.
- FastAPI verifies the token server-side using the current official Clerk guidance and configured keys/issuer details.
- The backend derives the authenticated Clerk user ID from the verified identity. Never trust a client-supplied `user_id` as proof of ownership.
- Protect saved user data at the API layer, not solely by hiding UI routes.
- Keep private keys/server secrets exclusively in backend environment variables.

### Database approach

Recommended: PostgreSQL + SQLAlchemy 2.x + Alembic migrations.

Candidate logical entities:

- `datasets`: id, owner_clerk_user_id, original_filename, storage_key, status, row_count, column_names JSON/JSONB, created_at, updated_at.
- `analysis_runs`: id, dataset_id, owner_clerk_user_id (or ownership derivable with enforced join), analysis_version, status, metrics JSONB, warnings JSONB, created_at.
- `model_runs` (optional): id, owner/reference, dataset/analysis reference, model_version, target_name, evaluation_metrics JSONB, created_at.

The final schema should be normalized where appropriate and have foreign keys, indexes, migration scripts, and ownership-safe query paths. Do not store large CSV file bodies directly in PostgreSQL by default. For a local student demo, files can live in a controlled, gitignored local storage directory with their metadata in PostgreSQL. A deployed version should use managed/object storage and a storage abstraction.

### User isolation

Every query for user-owned data must be scoped to the verified identity. Test that User A cannot view, download, delete, or analyze User B's dataset by changing a path ID or request body. Return appropriate `401`/`403`/`404` responses without leaking whether another user's record exists.

## 10. Configuration

Example frontend `.env.example`:

```dotenv
VITE_API_BASE_URL=http://localhost:8000
# Add the Clerk publishable key only in the authentication phase.
# VITE_CLERK_PUBLISHABLE_KEY=
```

Example backend `.env.example`:

```dotenv
APP_ENV=development
FRONTEND_ORIGIN=http://localhost:5173
MAX_UPLOAD_SIZE_MB=10
UPLOAD_DIR=./uploads
# Phase 3 only:
# DATABASE_URL=postgresql+psycopg://USER:PASSWORD@localhost:5432/creatorlens
# CLERK_JWKS_URL=
# CLERK_ISSUER=
```

These are examples, not real credentials. Choose the exact Clerk verification configuration according to the current official SDK/documentation. `.env` files must be gitignored. Never commit database credentials, Clerk secret keys, or private dataset files.

## 11. Error Handling and Observability

- Return clear validation errors for unsupported file type, oversized files, empty CSVs, parsing failures, missing required fields, and unsupported analyses.
- Log technical details server-side without logging tokens, secrets, or unnecessary personal data.
- Return a correlation/request ID if practical for troubleshooting.
- Avoid returning stack traces to clients.
- Use stable error structures, for example `{ "detail": "CSV could not be parsed" }`, consistent with FastAPI's response conventions.

## 12. Testing Strategy

### Frontend
- Type check and production build.
- Route rendering and navigation checks.
- Loading/error/empty states.
- API service error handling.
- Upload component validation and response display.

### Backend
- Health endpoint test.
- Valid, malformed, empty, oversized, and unsupported upload tests.
- Data-cleaning tests for missing values, duplicates, dates, bad types, zero denominators, and missing columns.
- Metric unit tests against small known input examples.
- Tests that API responses are JSON-serializable and do not contain NaN/Infinity.

### Authentication and database (Phase 3)
- Valid and invalid token tests.
- Unauthenticated access to protected endpoints.
- Ownership/tenant isolation tests.
- Migration and persistence tests.
- CRUD tests for the supported saved records.

## 13. Local Development Commands

Commands may vary slightly based on generated package scripts and Python environment. Update this section after the repository is created and tested.

Backend (from `backend/`):

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Install dependencies after requirements.txt exists:
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Frontend (from `frontend/`):

```bash
npm install
npm run dev
```

Typical local addresses are `http://localhost:5173` for Vite, `http://localhost:8000` for FastAPI, and `http://localhost:8000/docs` for development API docs. Verify these against actual configuration.

## 14. Definition of Done

A feature is complete only when:

- Its behavior matches its requirement and visible UI states.
- Data is real, labelled demo data, or unavailable as appropriate—never silently fabricated.
- Types/validation and errors are handled.
- Relevant tests or reproducible manual verification have been performed.
- Documentation and `.env.example` are updated if configuration changes.
- Secrets and private datasets are not committed.
- The frontend build and backend startup succeed after the change.

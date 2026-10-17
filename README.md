# CreatorLens

CreatorLens is a student project for reviewing social-media post performance from CSV data. This workspace currently contains the Phase 1 foundation: a React frontend and a FastAPI backend.

Phase 1 is explicit about what is real:

- Dashboard, analytics, and insights numbers come from the built-in demo file `backend/app/data/demo_posts.csv`. Every demo response includes `"is_demo": true`.
- `POST /api/upload` validates a real CSV in memory. It does not save the file and does not run an analysis.
- `POST /api/documents` analyses a CSV, PDF, or DOCX file and saves it in a local SQLite database. CSV numbers are calculated in Python. A Gemini summary is added only when `GEMINI_API_KEY` is set.
- There is no locally trained model and no PostgreSQL database. Accounts use the local SQLite auth store.
- Video analysis is a separate backend path. It calls the Gemini API only when `GEMINI_API_KEY` is set on the server. The CSV dashboard does not use it.

The product and architecture notes live in `CreatorLens_Docs/`.

## Engagement rate

Every screen and endpoint uses one definition:

`view_based_engagement_rate = (likes + comments + shares) / views * 100`

The average is the mean of those per-post rates. A post with missing or non-positive views is left out of the average. Missing likes, comments, or shares are not treated as zero.

## Requirements

- Windows PowerShell
- Python 3.14 (the versions in `backend/requirements.txt` were installed with 3.14.4)
- Node.js 24 and npm

## Backend

From the workspace root:

```powershell
cd C:\Users\anshi\OneDrive\Desktop\CretorLens\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

If activation is blocked by the execution policy, run this in that same window and then activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

You can also call the virtual environment without activating it:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

API: `http://localhost:8000`  
Interactive docs: `http://localhost:8000/docs`

Tests, from `backend` with the virtual environment active:

```powershell
pytest
```

Or, without activation:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Optional settings are in `backend/.env.example`. The defaults already match local development, so a `.env` file is not required for the CSV API. `MAX_UPLOAD_SIZE_MB` defaults to 5. `FRONTEND_ORIGIN` defaults to `http://localhost:5173`. The API also allows `http://127.0.0.1:5173` because that is the same Vite dev server.

Video analysis needs a server-side key. From `backend`, copy the example if you do not already have a `.env` file, then set `GEMINI_API_KEY` in that file or in the shell. Do not put the key in `frontend/.env` or in any `VITE_` variable.

```powershell
cd C:\Users\anshi\OneDrive\Desktop\CretorLens\backend
Copy-Item .env.example .env
# Edit .env and set GEMINI_API_KEY. Leave it blank to keep video analysis disabled.
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

`GET /api/ai/status` reports whether the key and SDK are present. It does not call Gemini and does not return the key. `POST /api/videos/analyze` returns an error instead of an analysis when the key is missing.

Public YouTube metadata is read with `yt-dlp` on the server. A YouTube Data API key is not required. `YOUTUBE_CACHE_SECONDS` defaults to 21600. `GEMINI_API_KEY` is still required for written suggestions. `YOUTUBE_OAUTH_CLIENT_ID` and `YOUTUBE_OAUTH_CLIENT_SECRET` are reserved for a later creator connection and are not used yet.

An analytics CSV does not need a YouTube key. Preview it, then analyze it, from Analyze YouTube. A sample with ten dated rows is `backend/app/data/sample_video_analytics.csv`. A forecast is trained only when one video has at least eight dated view counts. One public snapshot is stored without a trained model. Engagement from a file is `(likes + comments) / views × 100`, or `(likes + comments + shares) / views × 100` when the shares column is present. Missing counts stay missing.

## Frontend

Open a second PowerShell window:

```powershell
cd C:\Users\anshi\OneDrive\Desktop\CretorLens\frontend
Copy-Item .env.example .env
npm install
npm run dev
```

App: `http://localhost:5173`

Vite is set to port 5173 only. If that port is already in use, stop the other process before starting the frontend. `frontend/.env` is only the public API address (`VITE_API_BASE_URL=http://localhost:8000`). It is not a secret. `.env` files are gitignored; `.env.example` is the file to copy.

Production check:

```powershell
npm run build
```

## Try a CSV upload

With the API running:

```powershell
curl.exe -X POST http://localhost:8000/api/upload -F "file=@C:\Users\anshi\OneDrive\Desktop\CretorLens\backend\app\data\demo_posts.csv"
```

A successful response reports the filename, size, row count, and column names. It also says the file was not saved and that no analysis was run. An empty file, a non-CSV extension, and a CSV with an unclosed quote are rejected.

## API routes in this phase

| Method | Path | What it returns |
|---|---|---|
| GET | `/api/health` | `{ "status": "ok", "service": "creatorlens-api" }` |
| GET | `/api/dashboard/summary` | Demo KPI summary |
| GET | `/api/dashboard/trends` | Demo weekly engagement series |
| GET | `/api/dashboard/content-comparison` | Demo category and platform comparison |
| GET | `/api/posts` | Demo posts, newest first |
| GET | `/api/insights` | Demo insight cards calculated from the same file |
| POST | `/api/upload` | CSV metadata only. The file is not saved. |
| POST | `/api/documents` | Analyse and save a CSV, PDF, or DOCX file |
| GET | `/api/documents` | Saved analyses |
| GET | `/api/documents/{id}` | One saved analysis |
| POST | `/api/documents/{id}/questions` | Ask a question about a saved document |
| GET | `/api/ai/status` | Whether Gemini is configured, without the API key |
| POST | `/api/videos/analyze` | One uploaded video file sent to Gemini, or an error if it is not configured |
| POST | `/api/youtube/preview` | Public metadata and statistics for one YouTube URL |
| POST | `/api/youtube/analyses` | Save that public snapshot, metrics, and an optional Gemini narrative |
| POST | `/api/youtube/analyses/{id}/refresh` | Fetch the video again and save a new snapshot |
| POST | `/api/youtube/analyses/{id}/roast` | Roast one saved video from its public counts. `style` is `friendly`, `savage`, or `brutal`. `force` asks for another take. |
| POST | `/api/youtube/analyses/{id}/roast/challenge` | Reassess a roast after a question. It does not automatically defend the first verdict. |
| POST | `/api/youtube/analyses/{id}/roast/fix` | Draft title, thumbnail, and hook alternatives for a roast. |
| POST | `/api/youtube/analyses/{id}/experiment` | Save the roast's next move as one experiment |
| POST | `/api/youtube/analyses/{id}/experiment/result` | Record a note, a later view count, or that the task was done. That is not a measured improvement. |
| GET | `/api/youtube/analyses` | Saved YouTube analyses |
| GET | `/api/youtube/analyses/{id}` | One saved YouTube analysis |
| GET | `/api/youtube/oauth/status` | Creator OAuth is not connected; retention stays empty |
| POST | `/api/analytics/preview` | Validate an analytics CSV and return a preview |
| POST | `/api/analytics/analyses` | Calculate metrics, an eligible forecast, and optional Gemini suggestions |
| GET | `/api/analytics/analyses` | Saved analytics CSV analyses |
| GET | `/api/analytics/analyses/{id}` | One saved analytics CSV analysis |

The dashboard routes accept optional `category`, `platform`, `start_date`, and `end_date` query parameters. Dates use `YYYY-MM-DD`. An unknown category returns an empty demo result rather than invented rows.

## Accounts

Registration, email verification, login, logout, and password reset use `backend/data/auth.sqlite`. Passwords are stored as PBKDF2-SHA256 hashes. The session is an HttpOnly `cl_session` cookie. State-changing requests from a signed-in browser send `X-CSRF-Token` from memory, not from localStorage. The Vite dev server proxies `/api` to `http://127.0.0.1:8000` so that cookie stays on the app origin.

Set `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM`, and `SMTP_TLS` to deliver verification and reset mail. When `SMTP_HOST` is empty and `APP_ENV` is not `production`, the link is written to the server log and to `email_outbox` so local checks can read it. The API never returns the token. Production without SMTP does not send mail, and an unverified account cannot open saved analyses.

Saved YouTube analyses, documents, analytics files, diagnoses, and experiments are queried with the user id from the session. Rows whose `user_id` is null stay in the database and are not visible to any account. They are not assigned to the first person who registers.

## Not in this phase

PostgreSQL, SQLAlchemy, and scikit-learn are intentionally absent. Saved document, YouTube, and analytics-file analyses use local SQLite files in `backend/data`, which is not committed. Public YouTube metadata is extracted with `yt-dlp` and does not use a YouTube Data API key. Transcripts, impressions, click-through rate, and audience retention from YouTube stay unavailable until a creator connects through OAuth. A view forecast is trained only when one video has at least eight dated view counts. A single public snapshot is stored without a trained forecast. Gemini suggestions are omitted, not invented, when `GEMINI_API_KEY` is missing.

Try the sample analytics file from the Analyze YouTube page:

```powershell
# The file is backend\app\data\sample_video_analytics.csv
# Preview it in the app, then choose Analyze file.
```

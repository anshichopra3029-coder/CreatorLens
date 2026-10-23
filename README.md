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

An analytics CSV does not need a YouTube key. Preview it, then analyze it, from Analyze YouTube. A sample with ten dated rows is `backend/app/data/sample_video_analytics.csv`. A forecast is made when one video has at least three dated view counts (see "Views forecast" below). One public snapshot is stored without a trained model. Engagement from a file is `(likes + comments) / views × 100`, or `(likes + comments + shares) / views × 100` when the shares column is present. Missing counts stay missing.

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
| GET | `/api/youtube/videos` | Saved videos, one row each, with recorded view-count totals |
| GET | `/api/youtube/videos/{video_id}/forecast` | Holt versus baseline forecast from the video's dated view counts |
| POST | `/api/youtube/videos/{video_id}/snapshot` | Record the current public view count (at most once per hour) |
| POST | `/api/youtube/videos/{video_id}/observations` | Import dated view history from a CSV (`observed_at,views`) |
| POST | `/api/predictions/train` | Train the engagement-rate model from a saved posts CSV (`{"source": "document", "document_id": "..."}`) or the demo posts (`{"source": "demo"}`) |
| GET | `/api/predictions/models` | Trained engagement-rate models with their held-out scores |
| GET | `/api/predictions/models/{id}` | One trained model's evaluation, importance, and limitations |
| POST | `/api/predictions/models/{id}/predict` | Predict a planned post's engagement rate from platform, category, posting date, title, and duration |

The dashboard routes accept optional `category`, `platform`, `start_date`, and `end_date` query parameters. Dates use `YYYY-MM-DD`. An unknown category returns an empty demo result rather than invented rows.

## Accounts

Registration, email verification, login, logout, and password reset use `backend/data/auth.sqlite`. Passwords are stored as PBKDF2-SHA256 hashes. The session is an HttpOnly `cl_session` cookie. State-changing requests from a signed-in browser send `X-CSRF-Token` from memory, not from localStorage. The Vite dev server proxies `/api` to `http://127.0.0.1:8000` so that cookie stays on the app origin.

Set `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM`, and `SMTP_TLS` to deliver verification and reset mail. When `SMTP_HOST` is empty and `APP_ENV` is not `production`, the link is written to the server log and to `email_outbox` so local checks can read it. The API never returns the token. Production without SMTP does not send mail, and an unverified account cannot open saved analyses.

Saved YouTube analyses, documents, analytics files, diagnoses, and experiments are queried with the user id from the session. Rows whose `user_id` is null stay in the database and are not visible to any account. They are not assigned to the first person who registers.

## Views forecast

Predictions → Saved sources lists each saved video once. **Show forecast** calls `GET /api/youtube/videos/{video_id}/forecast`, which reads every dated view count for that video and compares two methods:

- **Baseline**: future views equal the latest recorded count.
- **Holt's linear exponential smoothing** (`statsmodels`): a smoothed level plus a smoothed trend, updated at every observation.

Snapshots are irregular, so cumulative views are resampled onto a regular grid (1, 3, 6, 12, or 24 hours, the largest step not longer than the median gap) by straight-line interpolation between real observations. Data rules: fewer than 3 distinct timestamps gives no forecast; 3–5 gives a provisional baseline forecast; from 6, a rolling-origin back-test (each origin has at least 4 earlier observations and is scored on the real observations within the next 7 days) compares MAE and error relative to real growth. Holt's model is selected only when its MAE is at least 10% lower than the baseline's. Horizons (24 hours, 3 days, 7 days) longer than twice the recorded history are hidden, and forecasts never go below the latest count. No uncertainty interval is drawn.

View counts come from saved analyses (a cached re-analysis with identical counts is not counted again, and is no longer saved twice), from **Record a snapshot now** (`POST /api/youtube/videos/{id}/snapshot`, at most once per hour, bypasses the metadata cache), and from a CSV import (`POST /api/youtube/videos/{id}/observations`):

```csv
observed_at,views
2026-10-01T09:00:00Z,1200
2026-10-02T09:00:00Z,1850
2026-10-03,2400
```

`observed_at` is ISO 8601 (a date alone means 00:00 UTC, a time without a zone is read as UTC, future times are rejected). `views` is a whole number of at least 0. An optional `video_id` column must match the video. Repeated timestamps in a file are rejected; timestamps already stored are skipped. To collect snapshots for every saved video on a schedule (for example Windows Task Scheduler), run from `backend`:

```bash
python -m app.services.view_history --collect
```

## Engagement rate model

The Predictions page can train a model that estimates a planned post's engagement rate, `(likes + comments + shares) / views × 100` (or `(likes + comments) / views × 100` when the file has no shares column). Inputs are limited to fields known before publishing: platform, category, posting date (`post_datetime`, `posting_date`, `date`, …), posting hour (`posting_hour`), title, and duration. A CSV uploaded on Upload Dataset is checked for these columns when it is saved; `GET /api/predictions/datasets` lists every saved CSV with whether it can train and why not. Views, likes, comments, shares, followers gained, and other outcome columns are never used as inputs.

Training compares a mean baseline, a decision tree, a random forest, and XGBoost on the same held-out posts. The split is chronological when posting dates exist (the latest 20%, at least 6 posts). The model with the lowest held-out MAE is refit on every usable post and saved with its scikit-learn preprocessing pipeline to `backend/data/models` (not committed). If no model beats the mean baseline, the model is saved for inspection but refuses to predict. Training needs at least 30 usable posts; the 16 built-in demo posts are not enough, so the demo option returns that message instead of a model.

Train from the page after uploading a posts CSV on Upload Dataset, or from `backend`:

```bash
python -m app.services.engagement_model --csv path/to/posts.csv
python -m app.services.engagement_model --document <saved CSV document id>
```

Each prediction shows the typical held-out error, the training average for matching groups, and, when XGBoost is selected, per-input TreeSHAP contributions from XGBoost itself. Importance and group averages are associations in the training file, not causes.

## Not in this phase

PostgreSQL and SQLAlchemy are intentionally absent. Saved document, YouTube, and analytics-file analyses use local SQLite files in `backend/data`, which is not committed. Public YouTube metadata is extracted with `yt-dlp` and does not use a YouTube Data API key. Transcripts, impressions, click-through rate, and audience retention from YouTube stay unavailable until a creator connects through OAuth. A single public snapshot is stored without a trained forecast. Gemini suggestions are omitted, not invented, when `GEMINI_API_KEY` is missing.

Try the sample analytics file from the Analyze YouTube page:

```powershell
# The file is backend\app\data\sample_video_analytics.csv
# Preview it in the app, then choose Analyze file.
```

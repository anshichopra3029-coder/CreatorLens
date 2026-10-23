"""Draw the CreatorLens synopsis diagrams from the verified repository structure.

Run from the project root with a Python that has matplotlib:
    python CreatorLens_Synopsis_Output/source/diagrams.py
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle, Circle

OUT = Path(__file__).resolve().parents[1]
plt.rcParams["font.family"] = "Times New Roman"
DPI = 220
FONT_SCALE = 1.25

_original_text = matplotlib.axes.Axes.text


def _scaled_text(self, *args, **kwargs):
    if "fontsize" in kwargs:
        kwargs["fontsize"] = kwargs["fontsize"] * FONT_SCALE
    return _original_text(self, *args, **kwargs)


matplotlib.axes.Axes.text = _scaled_text

INK = "#1f2937"
BLUE = "#dbeafe"
BLUE_EDGE = "#1d4ed8"
GREEN = "#dcfce7"
GREEN_EDGE = "#15803d"
AMBER = "#fef3c7"
AMBER_EDGE = "#b45309"
GREY = "#f3f4f6"
GREY_EDGE = "#4b5563"
PURPLE = "#ede9fe"
PURPLE_EDGE = "#6d28d9"


def box(ax, x, y, w, h, title, lines=(), face=GREY, edge=GREY_EDGE, title_size=12, line_size=10, dashed=False):
    patch = FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
        linewidth=1.4, edgecolor=edge, facecolor=face, linestyle="--" if dashed else "-",
    )
    ax.add_patch(patch)
    ax.text(x + w / 2, y + h - 0.12, title, ha="center", va="top", fontsize=title_size, fontweight="bold", color=INK)
    for index, line in enumerate(lines):
        ax.text(x + w / 2, y + h - 0.48 - index * 0.27, line, ha="center", va="top", fontsize=line_size, color=INK)


def arrow(ax, start, end, label="", both=False, dashed=False, offset=(0, 0), label_size=9.5, color=INK, rad=0.0):
    style = "<|-|>" if both else "-|>"
    patch = FancyArrowPatch(
        start, end, arrowstyle=style, mutation_scale=14, linewidth=1.3, color=color,
        linestyle="--" if dashed else "-", connectionstyle=f"arc3,rad={rad}",
    )
    ax.add_patch(patch)
    if label:
        mx = (start[0] + end[0]) / 2 + offset[0]
        my = (start[1] + end[1]) / 2 + offset[1]
        ax.text(mx, my, label, ha="center", va="center", fontsize=label_size, color=INK,
                bbox={"facecolor": "white", "edgecolor": "none", "pad": 1.5})


def architecture() -> None:
    fig, ax = plt.subplots(figsize=(16, 11.5))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 11.5)
    ax.axis("off")

    box(ax, 0.3, 9.6, 3.0, 1.5, "Creator", ["Web browser", "(uploads files, pastes URLs,", "views results)"], face=GREY)

    box(ax, 4.0, 9.5, 11.6, 1.7, "Frontend: React 19 + TypeScript single-page app (Vite 8 dev server)", [
        "Pages: Landing, Dashboard, Upload Dataset, Analyze YouTube, Saved analyses, Analytics, Insights, Predictions, Settings",
        "React Router 7 (routing)  |  Recharts 3 (charts)  |  Tailwind CSS 4 (styling)  |  Lucide (icons)",
        "Calls the API with fetch/XHR on the same origin; Vite proxies /api to the backend",
    ], face=BLUE, edge=BLUE_EDGE, title_size=13, line_size=10.5)
    arrow(ax, (3.3, 10.35), (4.0, 10.35), both=True)

    box(ax, 0.3, 4.15, 15.3, 4.3, "", face="#ffffff", edge=GREEN_EDGE)
    ax.text(8.0, 8.38, "Backend: FastAPI 0.143 on Uvicorn (Python 3.14), REST/JSON endpoints under /api", ha="center", va="top",
            fontsize=12.5, fontweight="bold", color=INK)
    arrow(ax, (9.8, 9.5), (9.8, 8.45), label="HTTP / JSON  (/api/...)", both=True, offset=(1.45, 0))

    routers = [
        ("Dashboard", "demo data,\nCSV check"),
        ("Documents", "CSV/PDF/DOCX,\nquestions"),
        ("YouTube", "analysis, diagnosis,\nRoast My Video"),
        ("View forecast", "history, snapshots,\nCSV import"),
        ("Analytics CSV", "dated rows,\ndiagnosis"),
        ("Predictions", "train, list,\npredict"),
        ("Auth & account", "implemented,\nsign-in paused"),
    ]
    width = 2.05
    for index, (title, body) in enumerate(routers):
        x = 0.5 + index * 2.17
        dashed = title.startswith("Auth")
        patch = FancyBboxPatch((x, 6.6), width, 1.3, boxstyle="round,pad=0.02,rounding_size=0.06", linewidth=1.1,
                               edgecolor=GREEN_EDGE, facecolor=GREEN, linestyle="--" if dashed else "-")
        ax.add_patch(patch)
        ax.text(x + width / 2, 7.8, title, ha="center", va="top", fontsize=9.6, fontweight="bold", color=INK)
        ax.text(x + width / 2, 7.38, body, ha="center", va="top", fontsize=8.6, color=INK)
    ax.text(0.55, 6.47, "API routers", fontsize=9, style="italic", color=GREEN_EDGE)

    services = [
        ("Data processing", ["Pandas 2.3, NumPy 2.5", "CSV profiling, engagement", "rate, trends, outliers"]),
        ("Document extraction", ["pypdf 6.20", "python-docx 1.2"]),
        ("Diagnosis & Roast", ["evidence rules", "(optional Gemini rewrite,", "validated)"]),
        ("Engagement model", ["scikit-learn 1.9 Pipeline", "Mean, Decision Tree,", "Random Forest, XGBoost 3.4"]),
        ("View forecasting", ["statsmodels 0.15 Holt", "vs last-value baseline,", "rolling-origin back-test"]),
    ]
    for index, (title, lines) in enumerate(services):
        x = 0.5 + index * 3.03
        patch = FancyBboxPatch((x, 4.4), 2.85, 1.85, boxstyle="round,pad=0.02,rounding_size=0.06", linewidth=1.1,
                               edgecolor=PURPLE_EDGE, facecolor=PURPLE)
        ax.add_patch(patch)
        ax.text(x + 1.425, 6.15, title, ha="center", va="top", fontsize=10.5, fontweight="bold", color=INK)
        for line_index, line in enumerate(lines):
            ax.text(x + 1.425, 5.75 - line_index * 0.34, line, ha="center", va="top", fontsize=9.3, color=INK)
    ax.text(0.55, 4.27, "Service layer", fontsize=9, style="italic", color=PURPLE_EDGE)

    box(ax, 0.3, 0.45, 8.9, 3.1, "Local storage (backend/data, not committed to Git)", [
        "SQLite: youtube.sqlite (analyses, metadata cache, view observations)",
        "SQLite: documents.sqlite (documents, questions)",
        "SQLite: analytics.sqlite (analytics analyses)",
        "SQLite: auth.sqlite (users, sessions, email tokens, email outbox)",
        "files/ (saved uploads)    models/ (joblib model + JSON evaluation)",
        "Built-in demo dataset: backend/app/data/demo_posts.csv (16 labelled posts)",
    ], face=AMBER, edge=AMBER_EDGE, title_size=12, line_size=10.5)
    arrow(ax, (4.75, 4.15), (4.75, 3.55), label="read / write", both=True, offset=(0.75, 0))

    box(ax, 9.6, 1.45, 2.9, 2.1, "YouTube public\nvideo pages", ["", "read by yt-dlp", "2026.8.19 (public", "metadata, no API key)"],
        face=GREY, edge=GREY_EDGE, title_size=11, line_size=10)
    box(ax, 12.8, 1.45, 2.8, 2.1, "Google Gemini API\n(optional)", ["", "google-genai 2.30,", "server-side key; text", "summaries and wording"],
        face=GREY, edge=GREY_EDGE, title_size=11, line_size=10, dashed=True)
    arrow(ax, (11.05, 4.15), (11.05, 3.55), label="public metadata", offset=(0.95, 0))
    arrow(ax, (14.2, 4.15), (14.2, 3.55), label="prompts / text", both=True, dashed=True, offset=(0.85, 0))

    ax.text(8.0, 0.02, "Solid border = implemented and active.  Dashed border = optional or currently disabled.",
            ha="center", va="bottom", fontsize=10, style="italic", color=GREY_EDGE)
    fig.savefig(OUT / "CreatorLens_Architecture_Diagram.png", dpi=DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def process(ax, x, y, r, number, label):
    ax.add_patch(Circle((x, y), r, facecolor=BLUE, edgecolor=BLUE_EDGE, linewidth=1.4))
    ax.text(x, y + r * 0.45, number, ha="center", va="center", fontsize=10.5, fontweight="bold", color=BLUE_EDGE)
    ax.text(x, y - 0.08, label, ha="center", va="center", fontsize=10, color=INK)


def entity(ax, x, y, w, h, label):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=GREY, edgecolor=INK, linewidth=1.4))
    ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=11, fontweight="bold", color=INK)


def store(ax, x, y, w, h, code, label):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=AMBER, edgecolor="none"))
    ax.plot([x, x + w], [y + h, y + h], color=AMBER_EDGE, linewidth=1.4)
    ax.plot([x, x + w], [y, y], color=AMBER_EDGE, linewidth=1.4)
    ax.plot([x, x], [y, y + h], color=AMBER_EDGE, linewidth=1.4)
    ax.plot([x + 0.55, x + 0.55], [y, y + h], color=AMBER_EDGE, linewidth=1.0)
    ax.text(x + 0.275, y + h / 2, code, ha="center", va="center", fontsize=10, fontweight="bold", color=AMBER_EDGE)
    ax.text(x + 0.55 + (w - 0.55) / 2, y + h / 2, label, ha="center", va="center", fontsize=9.8, color=INK)


def dfd() -> None:
    fig, ax = plt.subplots(figsize=(16, 11))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 11)
    ax.axis("off")

    import math

    r = 0.82
    cx = 7.0
    rows = {1: 9.5, 2: 7.5, 3: 5.5, 4: 3.5, 5: 1.5}
    labels = {
        1: "Upload and\nvalidate dataset",
        2: "Calculate metrics\nand insights",
        3: "Train and predict\nengagement rate",
        4: "Analyse\nYouTube video",
        5: "Forecast\nfuture views",
    }

    def edge(number, target):
        y = rows[number]
        dx, dy = target[0] - cx, target[1] - y
        length = math.hypot(dx, dy)
        return (cx + r * dx / length, y + r * dy / length)

    entity(ax, 0.3, 0.6, 2.0, 9.8, "Creator")
    for number, y in rows.items():
        process(ax, cx, y, r, f"{number}.0", labels[number])

    flows = {
        1: ("CSV / PDF / DOCX file", "validation result, saved analysis"),
        2: ("dashboard filters, chosen analysis", "metrics, charts, insights"),
        3: ("chosen dataset, planned post", "evaluation, predicted rate"),
        4: ("YouTube video URL", "statistics, diagnosis, roast"),
        5: ("Show forecast, history CSV", "24 h / 3 d / 7 d forecast"),
    }
    for number, (incoming, outgoing) in flows.items():
        y = rows[number]
        left = cx - math.sqrt(r * r - 0.3 * 0.3)
        arrow(ax, (2.3, y + 0.3), (left, y + 0.3))
        arrow(ax, (left, y - 0.3), (2.3, y - 0.3))
        ax.text(3.95, y + 0.47, incoming, ha="center", va="center", fontsize=9.6, color=INK)
        ax.text(3.95, y - 0.47, outgoing, ha="center", va="center", fontsize=9.6, color=INK)

    store(ax, 10.0, 8.5, 3.4, 0.5, "D1", "documents.sqlite + files/")
    store(ax, 10.0, 5.25, 3.4, 0.5, "D3", "models/ (joblib + JSON)")
    store(ax, 3.0, 8.27, 2.6, 0.45, "D4", "demo_posts.csv")
    store(ax, 9.2, 1.25, 2.4, 0.5, "D2", "youtube.sqlite")

    arrow(ax, edge(1, (10.0, 8.85)), (10.0, 8.85), label="saved file + profile", offset=(0.25, 0.22))
    arrow(ax, (10.0, 8.5), edge(2, (10.0, 8.5)), label="saved analysis", offset=(0.55, -0.12))
    arrow(ax, (10.45, 8.5), edge(3, (10.45, 8.5)), label="saved posts CSV", offset=(0.95, 0.0))
    arrow(ax, (5.6, 8.3), edge(2, (5.6, 8.3)), label="demo posts", offset=(0.55, 0.22), label_size=9)
    arrow(ax, edge(3, (10.0, 5.5)), (10.0, 5.5), label="model saved / loaded", both=True, offset=(0, 0.2))
    arrow(ax, edge(4, (9.45, 1.75)), (9.45, 1.75), label="analysis +\nview count", offset=(-0.45, -0.2), label_size=9)
    arrow(ax, (9.2, 1.5), edge(5, (9.2, 1.5)), label="dated view counts", both=True, offset=(0.05, 0.22), label_size=9)

    entity(ax, 13.8, 0.2, 2.0, 1.15, "YouTube\n(public pages)")
    entity(ax, 13.8, 4.3, 2.0, 1.2, "Google Gemini\n(optional)")
    entity(ax, 13.8, 9.25, 2.0, 1.2, "Google Gemini\n(optional) *")
    arrow(ax, (13.8, 1.15), edge(4, (13.8, 1.15)), label="public metadata", offset=(0.4, 0.3))
    arrow(ax, (13.8, 0.65), edge(5, (13.8, 0.65)), label="current view count (snapshot)", offset=(0.9, -0.22))
    arrow(ax, edge(4, (13.8, 4.9)), (13.8, 4.9), label="prompt with evidence / rewritten text", both=True, dashed=True,
          offset=(0.6, 0.3))
    arrow(ax, edge(1, (13.8, 9.85)), (13.8, 9.85), label="extracted text / summary", both=True, dashed=True, offset=(0.4, 0.2))

    ax.text(8.0, 10.95, "Level-1 Data Flow Diagram of CreatorLens (implemented flows)", ha="center", va="center",
            fontsize=14, fontweight="bold", color=INK)
    ax.set_ylim(-0.45, 11)
    ax.text(8.0, -0.3,
            "Circle = process   Rectangle = external entity   Open box = data store   Dashed arrow = optional   "
            "* duplicate of the same external entity",
            ha="center", va="center", fontsize=10, style="italic", color=GREY_EDGE)
    fig.savefig(OUT / "CreatorLens_Data_Flow_Diagram.png", dpi=DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def table(ax, x, y_top, w, name, database, columns, face=BLUE, edge=BLUE_EDGE):
    row = 0.33
    header = 0.62
    height = header + row * len(columns) + 0.1
    ax.add_patch(Rectangle((x, y_top - height), w, height, facecolor="white", edgecolor=edge, linewidth=1.4))
    ax.add_patch(Rectangle((x, y_top - header), w, header, facecolor=face, edgecolor=edge, linewidth=1.4))
    ax.text(x + w / 2, y_top - 0.2, name, ha="center", va="center", fontsize=11.5, fontweight="bold", color=INK)
    ax.text(x + w / 2, y_top - 0.46, database, ha="center", va="center", fontsize=8.8, style="italic", color=GREY_EDGE)
    for index, column in enumerate(columns):
        ax.text(x + 0.12, y_top - header - 0.2 - index * row, column, ha="left", va="center", fontsize=9.6, color=INK)
    return (x, y_top - height, w, height)


def er() -> None:
    fig, ax = plt.subplots(figsize=(16, 11.5))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 11.5)
    ax.axis("off")
    ax.text(8.0, 11.25, "Entity-Relationship Diagram of the implemented SQLite schema", ha="center", fontsize=14,
            fontweight="bold", color=INK)

    ax.set_ylim(-0.6, 11.5)
    youtube = table(ax, 0.3, 10.6, 3.4, "youtube_analyses", "youtube.sqlite", [
        "PK  id : TEXT", "video_id : TEXT", "created_at : TEXT", "payload : TEXT (JSON)", "user_id : TEXT (nullable)",
    ])
    cache = table(ax, 4.7, 10.6, 3.3, "youtube_cache", "youtube.sqlite", [
        "PK  video_id : TEXT", "fetched_at : TEXT", "payload : TEXT (JSON)",
    ])
    analytics = table(ax, 8.6, 10.6, 3.0, "analytics_analyses", "analytics.sqlite", [
        "PK  id : TEXT", "created_at : TEXT", "payload : TEXT (JSON)", "user_id : TEXT (nullable)",
    ], face=PURPLE, edge=PURPLE_EDGE)
    documents = table(ax, 12.1, 10.6, 3.6, "documents", "documents.sqlite", [
        "PK  id : TEXT", "filename : TEXT", "format : TEXT", "size_bytes : INTEGER", "stored_path : TEXT",
        "created_at : TEXT", "payload : TEXT (JSON)", "user_id : TEXT (nullable)",
    ], face=AMBER, edge=AMBER_EDGE)
    observations = table(ax, 0.3, 7.5, 3.9, "view_observations", "youtube.sqlite", [
        "PK  id : INTEGER", "user_id : TEXT", "video_id : TEXT", "observed_at : TEXT", "views : INTEGER",
        "source : TEXT", "created_at : TEXT", "UNIQUE (user_id, video_id, observed_at)",
    ])
    users = table(ax, 5.4, 6.9, 3.6, "users", "auth.sqlite", [
        "PK  id : TEXT", "email : TEXT (unique)", "display_name : TEXT", "password_hash : TEXT",
        "email_verified_at : TEXT", "created_at : TEXT",
    ], face=GREEN, edge=GREEN_EDGE)
    questions = table(ax, 12.1, 6.5, 3.6, "questions", "documents.sqlite", [
        "PK  id : TEXT", "FK  document_id : TEXT", "question : TEXT", "answer : TEXT", "cited_evidence : TEXT",
        "uncertainty_note : TEXT", "created_at : TEXT",
    ], face=AMBER, edge=AMBER_EDGE)
    table(ax, 0.3, 2.9, 3.2, "email_outbox", "auth.sqlite", [
        "PK  id : INTEGER", "recipient : TEXT", "purpose : TEXT", "body : TEXT", "created_at : TEXT",
    ], face=GREEN, edge=GREEN_EDGE)
    table(ax, 4.0, 2.9, 3.3, "sessions", "auth.sqlite", [
        "PK  token_hash : TEXT", "FK  user_id : TEXT", "csrf_token : TEXT", "expires_at : TEXT",
    ], face=GREEN, edge=GREEN_EDGE)
    table(ax, 8.2, 2.9, 3.3, "email_tokens", "auth.sqlite", [
        "PK  token_hash : TEXT", "FK  user_id : TEXT", "purpose : TEXT", "expires_at : TEXT", "used_at : TEXT",
    ], face=GREEN, edge=GREEN_EDGE)
    del youtube, cache, analytics, documents, observations, users, questions

    def link(start, end, label, ends=("1", "N"), dashed=False, label_offset=(0.0, 0.0), end_offsets=((0.12, 0.0), (0.12, 0.0))):
        ax.plot([start[0], end[0]], [start[1], end[1]], color=INK, linewidth=1.4, linestyle="--" if dashed else "-")
        sx = start[0] + (end[0] - start[0]) * 0.12 + end_offsets[0][0]
        sy = start[1] + (end[1] - start[1]) * 0.12 + end_offsets[0][1]
        ex = start[0] + (end[0] - start[0]) * 0.88 + end_offsets[1][0]
        ey = start[1] + (end[1] - start[1]) * 0.88 + end_offsets[1][1]
        ax.text(sx, sy, ends[0], fontsize=10.5, fontweight="bold", ha="center", va="center")
        ax.text(ex, ey, ends[1], fontsize=10.5, fontweight="bold", ha="center", va="center")
        mx = (start[0] + end[0]) / 2 + label_offset[0]
        my = (start[1] + end[1]) / 2 + label_offset[1]
        ax.text(mx, my, label, ha="center", va="center", fontsize=9.4, style="italic", color=INK,
                bbox={"facecolor": "white", "edgecolor": "none", "pad": 1.0})

    link((6.4, 4.2), (5.65, 2.9), "has (FK)", label_offset=(-0.35, 0.0))
    link((8.0, 4.2), (9.85, 2.9), "has (FK)", label_offset=(0.4, 0.05))
    link((5.7, 6.9), (3.7, 8.45), "owns (logical)", dashed=True, label_offset=(0.1, 0.12),
         end_offsets=((0.0, 0.2), (0.0, 0.2)))
    link((5.4, 5.55), (4.2, 5.55), "owns", dashed=True, label_offset=(0.0, 0.25), end_offsets=((0.0, -0.2), (0.0, -0.2)))
    link((8.4, 6.9), (10.1, 8.56), "owns (logical)", dashed=True, label_offset=(0.0, 0.0),
         end_offsets=((0.2, 0.0), (0.2, 0.0)))
    link((9.0, 5.9), (12.1, 7.6), "owns (logical)", dashed=True, label_offset=(0.1, -0.05),
         end_offsets=((0.0, -0.22), (0.0, -0.22)))
    link((2.0, 8.23), (2.0, 7.5), "same video_id", ends=("1", "N"), dashed=True, label_offset=(1.0, 0.0),
         end_offsets=((0.2, 0.0), (0.2, 0.0)))
    link((3.7, 9.7), (4.7, 9.7), "video_id", ends=("N", "1"), dashed=True, label_offset=(0.0, 0.25),
         end_offsets=((0.0, -0.2), (0.0, -0.2)))
    link((13.9, 7.24), (13.9, 6.5), "has (FK)", label_offset=(0.75, 0.0), end_offsets=((0.22, 0.0), (0.22, 0.0)))

    ax.text(8.0, -0.4,
            "Solid line = enforced foreign key.   Dashed line = logical link by column value (no FK constraint).   "
            "user_id was added to the analysis tables by migration and is NULL for older rows.",
            ha="center", fontsize=10, style="italic", color=GREY_EDGE)
    fig.savefig(OUT / "CreatorLens_ER_Diagram.png", dpi=DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def gantt() -> None:
    done = "#2563eb"
    active = "#f59e0b"
    planned = "#9ca3af"
    tasks = [
        ("Requirement analysis and problem definition (PRD)", date(2026, 10, 14), 1, "done"),
        ("System design and architecture (TRD, architecture.md)", date(2026, 10, 14), 1, "done"),
        ("Frontend shell, demo dashboard and FastAPI foundation", date(2026, 10, 14), 2, "done"),
        ("CSV upload validation and document analysis", date(2026, 10, 15), 1, "done"),
        ("YouTube public-metadata analysis (yt-dlp)", date(2026, 10, 15), 2, "done"),
        ("Creator analytics CSV and performance diagnosis", date(2026, 10, 16), 1, "done"),
        ("Accounts and SQLite data ownership (now paused)", date(2026, 10, 17), 1, "done"),
        ("Roast My Video (creative feedback)", date(2026, 10, 17), 1, "done"),
        ("Engagement-rate model (scikit-learn, XGBoost)", date(2026, 10, 18), 1, "done"),
        ("View forecasting (Holt vs. last-value baseline)", date(2026, 10, 19), 2, "done"),
        ("Automated backend tests (142 tests)", date(2026, 10, 14), 7, "done"),
        ("Literature review and synopsis preparation", date(2026, 10, 21), 1, "active"),
        ("Integration testing and debugging", date(2026, 10, 22), 10, "planned"),
        ("Re-enable sign-in and verify per-user isolation", date(2026, 10, 27), 10, "planned"),
        ("Collect real creator data and evaluate models", date(2026, 10, 27), 14, "planned"),
        ("Final report, presentation and submission", date(2026, 11, 6), 9, "planned"),
    ]
    fig, ax = plt.subplots(figsize=(15, 8.2))
    for index, (name, start, days, status) in enumerate(tasks):
        y = len(tasks) - 1 - index
        color = {"done": done, "active": active, "planned": planned}[status]
        hatch = "//" if status == "planned" else None
        ax.barh(y, days, left=mdates.date2num(start), height=0.62, color=color, edgecolor="#374151",
                linewidth=0.8, hatch=hatch, alpha=0.95 if status != "planned" else 0.55)
    ax.set_yticks(range(len(tasks)))
    ax.set_yticklabels([task[0] for task in reversed(tasks)], fontsize=14)
    ax.xaxis_date()
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    ax.set_xlim(mdates.date2num(date(2026, 10, 13)), mdates.date2num(date(2026, 11, 16)))
    ax.tick_params(axis="x", labelsize=13, rotation=0)
    ax.grid(axis="x", color="#e5e7eb", linewidth=0.8)
    ax.set_axisbelow(True)
    today = mdates.date2num(date(2026, 10, 21)) + 0.5
    ax.axvline(today, color="#dc2626", linewidth=1.4, linestyle="--")
    ax.text(today + 0.15, len(tasks) - 0.35, "Synopsis date\n21 Oct 2026", color="#dc2626", fontsize=10, va="top")
    ax.set_xlabel("Calendar date, 2026 (time unit: days)", fontsize=15)
    ax.set_title("CreatorLens Project Timeline (Gantt Chart)", fontsize=18, fontweight="bold", pad=12)
    from matplotlib.patches import Patch

    ax.legend(
        handles=[
            Patch(facecolor=done, edgecolor="#374151", label="Completed (dated by Git commits and file timestamps)"),
            Patch(facecolor=active, edgecolor="#374151", label="In progress"),
            Patch(facecolor=planned, edgecolor="#374151", hatch="//", alpha=0.55, label="Proposed (estimated dates, to be confirmed)"),
        ],
        loc="upper right", fontsize=13, frameon=True,
    )
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "CreatorLens_Gantt_Chart.png", dpi=DPI, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    architecture()
    dfd()
    er()
    gantt()
    print("diagrams written to", OUT)

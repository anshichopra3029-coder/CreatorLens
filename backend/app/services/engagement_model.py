"""Train and serve the post engagement-rate model.

Target: view-based engagement rate, (likes + comments + shares) / views * 100,
or (likes + comments) / views * 100 when the file has no shares column.

Inputs are limited to fields known before a post is published: platform,
category, posting date, title, and duration. Views, likes, comments, shares,
and every other outcome column are excluded from the features.

A mean baseline, a decision tree, a random forest, and XGBoost are compared on
the same held-out posts. The split is chronological when posting dates exist.
The model with the lowest held-out MAE is refit on every usable row and saved
with its preprocessing pipeline. Prediction is refused when no model beat the
mean baseline.

Train from the command line (run from ``backend``):

    python -m app.services.engagement_model --csv path/to/posts.csv
    python -m app.services.engagement_model --document <saved CSV document id>
    python -m app.services.engagement_model --demo
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import re
from datetime import datetime, timezone
from functools import lru_cache
from importlib.metadata import version
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from app.core.config import settings
from app.schemas.engagement import (
    Contribution,
    EngagementModelInfo,
    EngagementPrediction,
    FeatureImportance,
    GroupObservation,
    HistoricalContext,
    ModelScore,
    PostsDatasetCheck,
    PredictionInput,
    TargetSummary,
    TrainingDataset,
)

logger = logging.getLogger(__name__)

MIN_TRAINING_ROWS = 30
MIN_HOLDOUT_ROWS = 6
HOLDOUT_FRACTION = 0.2
RANDOM_STATE = 42

_MODEL_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")

FEATURE_ALIASES: dict[str, tuple[str, ...]] = {
    "platform": ("platform", "network", "channel_platform"),
    "category": ("category", "content_type", "content_category", "post_type"),
    "posted_at": (
        "post_datetime", "posted_at", "posting_date", "published_at", "publish_date", "post_date", "upload_date", "date",
    ),
    "posting_hour": ("posting_hour", "post_hour", "hour_posted", "publish_hour"),
    "title": ("title", "caption", "headline"),
    "duration_seconds": ("duration_seconds", "duration", "length_seconds", "video_length_seconds"),
}
OUTCOME_ALIASES: dict[str, tuple[str, ...]] = {
    "views": ("views", "view_count", "plays"),
    "likes": ("likes", "like_count"),
    "comments": ("comments", "comment_count"),
    "shares": ("shares", "share_count"),
}
FEATURE_LABELS = {
    "platform": "Platform",
    "category": "Category",
    "posted_at": "Posting date",
    "posting_hour": "Posting hour (0-23)",
    "title": "Title",
    "duration_seconds": "Duration (seconds)",
}
CATEGORICAL = ("platform", "category")
MODEL_LABELS = {
    "dummy_mean": "Simple average (baseline)",
    "decision_tree": "Decision tree",
    "random_forest": "Random forest",
    "xgboost": "XGBoost",
}
_DERIVED_SOURCE = {
    "weekday": "posted_at",
    "month": "posted_at",
    "hour": "posted_at",
    "posting_hour": "posting_hour",
    "title_chars": "title",
    "title_words": "title",
    "title_has_number": "title",
    "title_is_question": "title",
    "duration_seconds": "duration_seconds",
}


class EngagementModelError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def models_dir() -> Path:
    path = settings.data_dir / "models"
    path.mkdir(parents=True, exist_ok=True)
    return path


def derive_features(frame: pd.DataFrame, features: list[str], use_hour: bool) -> pd.DataFrame:
    """Turn the raw pre-publication columns into model columns. Used at training and inference."""
    out = pd.DataFrame(index=frame.index)
    for name in CATEGORICAL:
        if name in features:
            values = frame[name].astype("string").str.strip()
            out[name] = values.where(values.notna() & (values != ""), "unknown").astype(str)
    if "posted_at" in features:
        stamps = pd.to_datetime(frame["posted_at"], errors="coerce", format="mixed")
        out["weekday"] = stamps.dt.dayofweek.astype(float)
        out["month"] = stamps.dt.month.astype(float)
        if use_hour:
            out["hour"] = stamps.dt.hour.astype(float)
    if "posting_hour" in features:
        hours = pd.to_numeric(frame["posting_hour"], errors="coerce")
        out["posting_hour"] = hours.where((hours >= 0) & (hours <= 23))
    if "title" in features:
        text = frame["title"].fillna("").astype(str)
        out["title_chars"] = text.str.len().astype(float)
        out["title_words"] = text.str.split().str.len().fillna(0).astype(float)
        out["title_has_number"] = text.str.contains(r"\d", regex=True).astype(float)
        out["title_is_question"] = text.str.contains(r"\?", regex=True).astype(float)
    if "duration_seconds" in features:
        out["duration_seconds"] = pd.to_numeric(frame["duration_seconds"], errors="coerce")
    return out


def train_from_frame(
    raw: pd.DataFrame,
    *,
    model_id: str,
    source_kind: str,
    source_id: str | None,
    source_label: str,
    testing_only: bool = False,
) -> EngagementModelInfo:
    _check_id(model_id)
    from sklearn.inspection import permutation_importance

    prepared = _prepare(raw)
    frame: pd.DataFrame = prepared["frame"]
    features: list[str] = prepared["features"]
    use_hour: bool = prepared["use_hour"]
    rows = len(frame)
    if rows < MIN_TRAINING_ROWS:
        raise EngagementModelError(
            422,
            f"Not enough data yet: training needs at least {MIN_TRAINING_ROWS} usable posts. This file has {rows} usable rows"
            f" ({prepared['dropped']} couldn't be used). No model was trained.",
        )

    holdout_rows = max(MIN_HOLDOUT_ROWS, math.ceil(rows * HOLDOUT_FRACTION))
    if "posted_at" in features:
        ordered = frame.assign(_stamp=pd.to_datetime(frame["posted_at"], errors="coerce", format="mixed"))
        ordered = ordered.sort_values("_stamp", kind="stable").drop(columns="_stamp")
        split = "chronological"
    else:
        ordered = frame.sample(frac=1.0, random_state=RANDOM_STATE)
        split = "random"
    train_part = ordered.iloc[: rows - holdout_rows]
    holdout_part = ordered.iloc[rows - holdout_rows :]
    holdout_start = None
    if split == "chronological":
        first = pd.to_datetime(holdout_part["posted_at"].iloc[0], errors="coerce", format="mixed")
        holdout_start = None if pd.isna(first) else first.date().isoformat()

    x_train, y_train = train_part[features], train_part["target"].to_numpy(dtype=float)
    x_hold, y_hold = holdout_part[features], holdout_part["target"].to_numpy(dtype=float)

    scores: list[ModelScore] = []
    fitted: dict[str, Any] = {}
    for name in MODEL_LABELS:
        pipeline = _pipeline(name, features, use_hour)
        pipeline.fit(x_train, y_train)
        predicted = pipeline.predict(x_hold)
        errors = predicted - y_hold
        scores.append(
            ModelScore(
                name=name,  # type: ignore[arg-type]
                label=MODEL_LABELS[name],
                mae=round(float(np.mean(np.abs(errors))), 4),
                rmse=round(float(np.sqrt(np.mean(errors**2))), 4),
            )
        )
        fitted[name] = pipeline

    baseline = next(score for score in scores if score.name == "dummy_mean")
    candidates = [score for score in scores if score.name != "dummy_mean"]
    best = min(candidates, key=lambda score: (score.mae, score.rmse))
    beats_baseline = best.mae < baseline.mae

    result = permutation_importance(
        fitted[best.name],
        x_hold,
        y_hold,
        scoring="neg_mean_absolute_error",
        n_repeats=20,
        random_state=RANDOM_STATE,
    )
    importance = sorted(
        (
            FeatureImportance(
                feature=feature,
                label=FEATURE_LABELS[feature],
                importance=round(float(result.importances_mean[index]), 4),
                spread=round(float(result.importances_std[index]), 4),
            )
            for index, feature in enumerate(features)
        ),
        key=lambda item: item.importance,
        reverse=True,
    )

    final = _pipeline(best.name, features, use_hour)
    final.fit(frame[features], frame["target"].to_numpy(dtype=float))

    target = frame["target"]
    observations = _observations(frame, features)
    limitations = [
        f"Learned from {rows} posts in {source_label}. Its estimates only reflect patterns in these posts.",
        f"We tested it on {holdout_rows} posts it hadn't learned from"
        + (" (your most recent ones)." if split == "chronological" else ", picked at random because the file has no posting dates."),
        "After testing, the chosen model learned from all usable posts, including the test posts.",
        "Which inputs matter most, and group averages, show patterns, not causes.",
    ]
    if rows < 100:
        limitations.append("Fewer than 100 posts were available, so its accuracy on new posts may differ from the test result.")
    if not beats_baseline:
        limitations.append(
            "No model did better than a simple average guess on the test posts, so this model won't make predictions."
        )
    if testing_only:
        limitations.insert(
            0,
            "Development/testing result from synthetic posts. These scores are not evidence of real-world predictive accuracy.",
        )

    info = EngagementModelInfo(
        model_id=model_id,
        source_kind=source_kind,  # type: ignore[arg-type]
        source_id=source_id,
        source_label=source_label,
        trained_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        target_formula=prepared["formula"],
        features=features,
        feature_labels={feature: FEATURE_LABELS[feature] for feature in features},
        categories={
            name: sorted(frame[name].dropna().astype(str).str.strip().replace("", np.nan).dropna().unique().tolist())
            for name in CATEGORICAL
            if name in features
        },
        rows_used=rows,
        rows_dropped=prepared["dropped"],
        drop_reasons=prepared["drop_reasons"],
        excluded_columns=prepared["excluded"],
        split=split,  # type: ignore[arg-type]
        train_rows=len(train_part),
        holdout_rows=holdout_rows,
        holdout_start=holdout_start,
        scores=scores,
        selected_model=best.name,
        selected_label=best.label,
        beats_baseline=beats_baseline,
        importance=importance,
        observations=observations,
        target_summary=TargetSummary(
            mean=round(float(target.mean()), 4),
            median=round(float(target.median()), 4),
            minimum=round(float(target.min()), 4),
            maximum=round(float(target.max()), 4),
        ),
        limitations=limitations,
        library_versions={name: version(name) for name in ("scikit-learn", "xgboost", "pandas", "numpy")},
    )
    _save(model_id, final, info, use_hour)
    return info


def predict(model_id: str, payload: PredictionInput) -> EngagementPrediction:
    artifact = _load(model_id)
    info = EngagementModelInfo.model_validate(artifact["info"])
    if not info.beats_baseline:
        raise EngagementModelError(
            409,
            "This model didn't do better than a simple average guess when we tested it, so it won't make predictions. "
            "Try training it on more posts.",
        )
    values = payload.model_dump()
    missing = [FEATURE_LABELS[name] for name in info.features if values.get(name) in (None, "")]
    if missing:
        raise EngagementModelError(422, f"Please fill in: {', '.join(missing)}.")
    warnings: list[str] = []
    if "posted_at" in info.features and pd.isna(pd.to_datetime(values["posted_at"], errors="coerce", format="mixed")):
        raise EngagementModelError(422, "We couldn't read the posting date. Use a date like 2026-10-18.")
    for name in CATEGORICAL:
        if name in info.features:
            known = info.categories.get(name, [])
            if str(values[name]).strip() not in known:
                warnings.append(
                    f"{FEATURE_LABELS[name]} '{values[name]}' wasn't in the posts the model learned from, so it's treated as new and unknown."
                )

    row = pd.DataFrame([{name: values[name] for name in info.features}])
    pipeline = artifact["pipeline"]
    try:
        raw_prediction = float(pipeline.predict(row)[0])
    except Exception as exc:
        logger.exception("Engagement prediction failed.")
        raise EngagementModelError(500, "Something went wrong while making this prediction. No prediction was made.") from exc
    if not math.isfinite(raw_prediction):
        raise EngagementModelError(500, "The model gave an unusable result. No prediction was made.")
    prediction = raw_prediction
    if prediction < 0:
        prediction = 0.0
        warnings.append("The model's estimate was below zero, so it's shown as 0, the lowest possible rate.")

    selected = next(score for score in info.scores if score.name == info.selected_model)
    base_value, contributions, note = _contributions(pipeline, row, info)
    matching = [
        item
        for item in info.observations
        if item.feature in CATEGORICAL and str(values.get(item.feature, "")).strip() == item.value
    ]
    return EngagementPrediction(
        model_id=info.model_id,
        model_name=info.selected_model,
        model_label=info.selected_label,
        target=info.target,
        target_formula=info.target_formula,
        target_unit=info.target_unit,
        predicted_engagement_rate=round(prediction, 2),
        typical_error=round(selected.mae, 2),
        band_low=round(max(0.0, prediction - selected.mae), 2),
        band_high=round(prediction + selected.mae, 2),
        inputs_used={name: values[name] for name in info.features},
        warnings=warnings,
        base_value=base_value,
        contributions=contributions,
        contribution_note=note,
        historical=HistoricalContext(
            training_mean=round(info.target_summary.mean, 2),
            training_median=round(info.target_summary.median, 2),
            matching_groups=matching,
        ),
    )


def list_models() -> list[EngagementModelInfo]:
    items: list[EngagementModelInfo] = []
    for path in models_dir().glob("*.json"):
        try:
            items.append(EngagementModelInfo.model_validate_json(path.read_text(encoding="utf-8")))
        except ValueError:
            logger.warning("Skipped an unreadable model description: %s", path.name)
    items.sort(key=lambda item: item.trained_at, reverse=True)
    return items


def get_model(model_id: str) -> EngagementModelInfo:
    _check_id(model_id)
    path = models_dir() / f"{model_id}.json"
    if not path.is_file():
        raise EngagementModelError(404, _missing_message(model_id))
    return EngagementModelInfo.model_validate_json(path.read_text(encoding="utf-8"))


def check_posts_dataset(raw: pd.DataFrame) -> PostsDatasetCheck:
    """Report whether a CSV can train the model, without training it."""
    total = len(raw)
    try:
        prepared = _prepare(raw)
    except EngagementModelError as exc:
        columns = {re.sub(r"[^a-z0-9]+", "_", str(column).strip().lower()).strip("_") for column in raw.columns}
        missing = [
            name for name in ("views", "likes", "comments") if not any(alias in columns for alias in OUTCOME_ALIASES[name])
        ]
        return PostsDatasetCheck(
            eligible=False,
            total_rows=total,
            min_rows=MIN_TRAINING_ROWS,
            missing_columns=missing,
            message=exc.detail.replace(" No model was trained.", ""),
        )
    rows = len(prepared["frame"])
    features = prepared["features"]
    labels = ", ".join(FEATURE_LABELS[name] for name in features)
    if rows < MIN_TRAINING_ROWS:
        reasons = " ".join(prepared["drop_reasons"])
        return PostsDatasetCheck(
            eligible=False,
            total_rows=total,
            usable_rows=rows,
            min_rows=MIN_TRAINING_ROWS,
            features=features,
            message=(
                f"Only {rows} of {total} rows are usable posts. Training needs at least {MIN_TRAINING_ROWS} posts with more "
                f"than zero views and with likes and comments filled in. {reasons}"
            ).strip(),
        )
    return PostsDatasetCheck(
        eligible=True,
        total_rows=total,
        usable_rows=rows,
        min_rows=MIN_TRAINING_ROWS,
        features=features,
        message=f"{rows} usable posts. The model can learn from: {labels}.",
    )


def list_training_datasets(user_id: str) -> list[TrainingDataset]:
    from app.services.document_store import files_dir, list_documents

    datasets: list[TrainingDataset] = []
    for item in list_documents(user_id):
        if item.format != "csv":
            continue
        path = files_dir() / f"{item.id}.csv"
        try:
            check = check_posts_dataset(read_posts_csv(path)) if path.is_file() else PostsDatasetCheck(
                eligible=False, message="The saved CSV file is missing from backend/data/files."
            )
        except EngagementModelError as exc:
            check = PostsDatasetCheck(eligible=False, message=exc.detail)
        datasets.append(TrainingDataset(document_id=item.id, filename=item.filename, created_at=item.created_at, check=check))
    return datasets


def read_posts_csv(path: Path) -> pd.DataFrame:
    from app.services.document_analysis import DocumentProcessError, _read_csv

    try:
        return _read_csv(path.read_bytes())
    except DocumentProcessError as exc:
        raise EngagementModelError(exc.status_code, exc.detail) from exc


def _prepare(raw: pd.DataFrame) -> dict[str, Any]:
    frame = raw.copy()
    frame.columns = [re.sub(r"[^a-z0-9]+", "_", str(column).strip().lower()).strip("_") for column in frame.columns]
    columns = set(frame.columns)

    def pick(aliases: tuple[str, ...]) -> str | None:
        return next((alias for alias in aliases if alias in columns), None)

    outcome_cols = {name: pick(aliases) for name, aliases in OUTCOME_ALIASES.items()}
    missing = [name for name in ("views", "likes", "comments") if outcome_cols[name] is None]
    if missing:
        raise EngagementModelError(
            422,
            f"This file isn't a list of posts the model can learn from. Missing column(s): {', '.join(missing)}. "
            "To work out engagement we need views, likes, and comments (shares are optional). No model was trained.",
        )
    feature_cols = {name: pick(aliases) for name, aliases in FEATURE_ALIASES.items()}
    features = [name for name, column in feature_cols.items() if column is not None]
    if not features:
        raise EngagementModelError(
            422,
            "The file has nothing known before posting (pre-publication columns) to learn from. Add platform, "
            "category, a posting date, a title, or a duration. Results such as views and likes are never used as "
            "inputs. No model was trained.",
        )

    data = pd.DataFrame(index=frame.index)
    for name, column in outcome_cols.items():
        if column is not None:
            data[name] = pd.to_numeric(frame[column].astype(str).str.replace(",", "", regex=False).str.strip(), errors="coerce")
    for name in features:
        data[name] = frame[feature_cols[name]]
    for name in ("duration_seconds", "posting_hour"):
        if name in features:
            data[name] = pd.to_numeric(data[name], errors="coerce")

    has_shares = outcome_cols["shares"] is not None
    counts = ["likes", "comments"] + (["shares"] if has_shares else [])
    reasons: list[str] = []
    keep = pd.Series(True, index=data.index)
    bad_views = data["views"].isna() | (data["views"] <= 0)
    if bad_views.any():
        reasons.append(f"{int(bad_views.sum())} rows had no views or zero views.")
    keep &= ~bad_views
    bad_counts = data[counts].isna().any(axis=1) | (data[counts] < 0).any(axis=1)
    if (bad_counts & keep).any():
        reasons.append(f"{int((bad_counts & keep).sum())} rows had a missing or negative like, comment, or share count.")
    keep &= ~bad_counts

    use_hour = False
    if "posted_at" in features:
        stamps = pd.to_datetime(data["posted_at"].astype(str), errors="coerce", format="mixed")
        parsed_share = float(stamps[keep].notna().mean()) if keep.any() else 0.0
        if parsed_share >= 0.9:
            bad_dates = stamps.isna() & keep
            if bad_dates.any():
                reasons.append(f"{int(bad_dates.sum())} rows had a posting date we couldn't read.")
            keep &= stamps.notna()
            kept = stamps[keep]
            use_hour = bool(((kept.dt.hour != 0) | (kept.dt.minute != 0)).any())
        else:
            features.remove("posted_at")
            data = data.drop(columns="posted_at")
            reasons.append("More than 1 in 10 posting dates couldn't be read, so dates weren't used.")

    data = data.loc[keep].copy()
    data["target"] = data[counts].sum(axis=1) / data["views"] * 100
    finite = np.isfinite(data["target"])
    data = data.loc[finite]
    known_outcomes = {
        "views", "view_count", "plays", "likes", "like_count", "comments", "comment_count", "shares", "share_count",
        "saves", "followers_gained", "subscribers_gained", "reach", "impressions", "watch_time", "ctr",
        "engagement_rate", "retention", "average_view_duration", "post_id", "postid", "id",
    }
    excluded = sorted(column for column in columns if column in known_outcomes)
    formula = "(likes + comments + shares) / views * 100" if has_shares else "(likes + comments) / views * 100"
    return {
        "frame": data,
        "features": features,
        "use_hour": use_hour,
        "dropped": int(len(raw) - len(data)),
        "drop_reasons": reasons,
        "excluded": excluded,
        "formula": formula,
    }


def _pipeline(name: str, features: list[str], use_hour: bool) -> Any:
    from sklearn.compose import ColumnTransformer
    from sklearn.dummy import DummyRegressor
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.impute import SimpleImputer
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import FunctionTransformer, OneHotEncoder
    from sklearn.tree import DecisionTreeRegressor
    from xgboost import XGBRegressor

    categorical = [column for column in CATEGORICAL if column in features]
    numeric = [
        column
        for column in derive_features(pd.DataFrame(columns=features), features, use_hour).columns
        if column not in categorical
    ]
    transformers = []
    if categorical:
        transformers.append(("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical))
    if numeric:
        transformers.append(("num", SimpleImputer(strategy="median", keep_empty_features=True), numeric))
    estimators = {
        "dummy_mean": lambda: DummyRegressor(strategy="mean"),
        "decision_tree": lambda: DecisionTreeRegressor(max_depth=4, min_samples_leaf=3, random_state=RANDOM_STATE),
        "random_forest": lambda: RandomForestRegressor(
            n_estimators=300, min_samples_leaf=2, random_state=RANDOM_STATE, n_jobs=1
        ),
        "xgboost": lambda: XGBRegressor(
            n_estimators=300,
            max_depth=3,
            learning_rate=0.05,
            subsample=0.9,
            colsample_bytree=0.9,
            min_child_weight=2,
            reg_lambda=1.0,
            random_state=RANDOM_STATE,
            n_jobs=1,
        ),
    }
    return Pipeline(
        [
            ("features", FunctionTransformer(derive_features, kw_args={"features": features, "use_hour": use_hour})),
            ("prep", ColumnTransformer(transformers, remainder="drop", verbose_feature_names_out=True)),
            ("model", estimators[name]()),
        ]
    )


def _observations(frame: pd.DataFrame, features: list[str]) -> list[GroupObservation]:
    items: list[GroupObservation] = []
    for name in CATEGORICAL:
        if name not in features:
            continue
        labels = frame[name].astype("string").str.strip()
        grouped = frame.assign(_label=labels).dropna(subset=["_label"]).groupby("_label")["target"]
        for value, group in grouped:
            if str(value) == "":
                continue
            items.append(
                GroupObservation(feature=name, value=str(value), posts=int(len(group)), mean_rate=round(float(group.mean()), 2))
            )
    items.sort(key=lambda item: (item.feature, -item.mean_rate))
    return items


def _contributions(pipeline: Any, row: pd.DataFrame, info: EngagementModelInfo) -> tuple[float | None, list[Contribution] | None, str]:
    if info.selected_model != "xgboost":
        return (
            None,
            None,
            "A breakdown for this single prediction is only available when the XGBoost model was chosen. "
            f"This model is a {info.selected_label.lower()}. See 'Which inputs the model relies on' above for the overall picture.",
        )
    import xgboost as xgb

    transformed = pipeline[:-1].transform(row)
    names = list(pipeline.named_steps["prep"].get_feature_names_out())
    booster = pipeline.named_steps["model"].get_booster()
    values = booster.predict(xgb.DMatrix(np.asarray(transformed, dtype=float)), pred_contribs=True)[0]
    totals: dict[str, float] = {}
    for name, value in zip(names, values[:-1], strict=True):
        prefix, _, column = name.partition("__")
        source = next((cat for cat in CATEGORICAL if prefix == "cat" and column.startswith(f"{cat}_")), None)
        source = source or _DERIVED_SOURCE.get(column, column)
        totals[source] = totals.get(source, 0.0) + float(value)
    contributions = sorted(
        (Contribution(feature=key, label=FEATURE_LABELS.get(key, key), value=round(value, 3)) for key, value in totals.items()),
        key=lambda item: abs(item.value),
        reverse=True,
    )
    return (
        round(float(values[-1]), 3),
        contributions,
        "How much each input pushed this estimate up or down, in percentage points, starting from the model's "
        "starting value (technical: XGBoost TreeSHAP). They explain this model's number, not what would happen if "
        "you changed the post.",
    )


def _save(model_id: str, pipeline: Any, info: EngagementModelInfo, use_hour: bool) -> None:
    import joblib

    folder = models_dir()
    artifact = folder / f"{model_id}.joblib"
    description = folder / f"{model_id}.json"
    temp_artifact = artifact.with_suffix(".joblib.tmp")
    joblib.dump({"pipeline": pipeline, "info": info.model_dump(mode="json"), "use_hour": use_hour}, temp_artifact)
    temp_artifact.replace(artifact)
    temp_description = description.with_suffix(".json.tmp")
    temp_description.write_text(info.model_dump_json(indent=2), encoding="utf-8")
    temp_description.replace(description)
    _load_cached.cache_clear()


def _load(model_id: str) -> dict[str, Any]:
    _check_id(model_id)
    path = models_dir() / f"{model_id}.joblib"
    if not path.is_file():
        raise EngagementModelError(404, _missing_message(model_id))
    return _load_cached(str(path), path.stat().st_mtime_ns)


@lru_cache(maxsize=8)
def _load_cached(path: str, mtime_ns: int) -> dict[str, Any]:
    import joblib

    del mtime_ns
    artifact = joblib.load(path)
    if not isinstance(artifact, dict) or "pipeline" not in artifact or "info" not in artifact:
        raise EngagementModelError(500, "The saved model file can't be read. Please train the model again.")
    return artifact


def _check_id(model_id: str) -> None:
    if not _MODEL_ID.match(model_id):
        raise EngagementModelError(400, "That model id is not valid.")


def _missing_message(model_id: str) -> str:
    return (
        f"No trained model called '{model_id}' was found. Train one from a saved posts CSV on the Predictions page "
        "(advanced: python -m app.services.engagement_model --csv path/to/posts.csv)."
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Train the CreatorLens engagement-rate model.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--csv", type=Path, help="Path to a posts CSV.")
    group.add_argument("--document", help="Id of a saved CSV document in backend/data.")
    group.add_argument("--demo", action="store_true", help="Use the built-in demo posts.")
    parser.add_argument("--model-id", help="Name for the saved model (letters, digits, hyphens).")
    parser.add_argument(
        "--testing",
        action="store_true",
        help="Label this run as synthetic development data, not real-world accuracy.",
    )
    args = parser.parse_args(argv)
    try:
        if args.csv is not None:
            frame = read_posts_csv(args.csv)
            model_id = args.model_id or re.sub(r"[^a-z0-9-]+", "-", args.csv.stem.lower()).strip("-")[:60] or "file"
            info = train_from_frame(
                frame,
                model_id=model_id,
                source_kind="file",
                source_id=None,
                source_label=args.csv.name,
                testing_only=args.testing,
            )
        elif args.document:
            info = train_from_document(args.document, user_id="local", model_id=args.model_id)
        else:
            info = train_from_demo()
    except EngagementModelError as exc:
        print(f"Not trained: {exc.detail}")
        return 1
    print(json.dumps({
        "model_id": info.model_id,
        "rows_used": info.rows_used,
        "split": info.split,
        "selected": info.selected_model,
        "beats_baseline": info.beats_baseline,
        "scores": [score.model_dump() for score in info.scores],
    }, indent=2))
    return 0


def train_from_document(document_id: str, *, user_id: str, model_id: str | None = None) -> EngagementModelInfo:
    from app.services.document_store import files_dir, get_document

    if not re.fullmatch(r"[0-9a-f-]{8,64}", document_id):
        raise EngagementModelError(400, "That document id is not valid.")
    document = get_document(document_id, user_id)
    if document is None:
        raise EngagementModelError(404, "That saved document was not found.")
    if document.format != "csv":
        raise EngagementModelError(422, "Only a saved CSV can train the engagement model.")
    path = files_dir() / f"{document_id}.csv"
    if not path.is_file():
        raise EngagementModelError(404, "The saved CSV file is missing from backend/data/files.")
    return train_from_frame(
        read_posts_csv(path),
        model_id=model_id or f"doc-{document_id}",
        source_kind="document",
        source_id=document_id,
        source_label=document.filename,
    )


def train_from_demo() -> EngagementModelInfo:
    from app.services.demo_dataset import DEMO_CSV

    return train_from_frame(
        read_posts_csv(DEMO_CSV),
        model_id="demo",
        source_kind="demo",
        source_id=None,
        source_label="the built-in demo posts",
    )


if __name__ == "__main__":
    raise SystemExit(main())

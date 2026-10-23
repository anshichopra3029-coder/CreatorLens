export type ModelName = "dummy_mean" | "decision_tree" | "random_forest" | "xgboost";
export type ModelFeature = "platform" | "category" | "posted_at" | "posting_hour" | "title" | "duration_seconds";

export interface PostsDatasetCheck {
  eligible: boolean;
  total_rows: number;
  usable_rows: number;
  min_rows: number;
  features: ModelFeature[];
  missing_columns: string[];
  message: string;
}

export interface TrainingDataset {
  document_id: string;
  filename: string;
  created_at: string;
  check: PostsDatasetCheck;
}

export interface TrainingDatasetList {
  count: number;
  eligible_count: number;
  datasets: TrainingDataset[];
}

export interface ModelScore {
  name: ModelName;
  label: string;
  mae: number;
  rmse: number;
}

export interface FeatureImportance {
  feature: ModelFeature;
  label: string;
  importance: number;
  spread: number;
}

export interface GroupObservation {
  feature: string;
  value: string;
  posts: number;
  mean_rate: number;
}

export interface EngagementModelInfo {
  model_id: string;
  source_kind: "document" | "demo" | "file";
  source_id: string | null;
  source_label: string;
  trained_at: string;
  target: string;
  target_formula: string;
  target_unit: string;
  features: ModelFeature[];
  feature_labels: Record<string, string>;
  categories: Record<string, string[]>;
  rows_used: number;
  rows_dropped: number;
  drop_reasons: string[];
  excluded_columns: string[];
  split: "chronological" | "random";
  train_rows: number;
  holdout_rows: number;
  holdout_start: string | null;
  scores: ModelScore[];
  selected_model: ModelName;
  selected_label: string;
  beats_baseline: boolean;
  importance: FeatureImportance[];
  observations: GroupObservation[];
  target_summary: { mean: number; median: number; minimum: number; maximum: number };
  limitations: string[];
  library_versions: Record<string, string>;
}

export interface EngagementModelList {
  count: number;
  models: EngagementModelInfo[];
}

export interface PredictionInput {
  platform?: string;
  category?: string;
  posted_at?: string;
  posting_hour?: number;
  title?: string;
  duration_seconds?: number;
}

export interface Contribution {
  feature: string;
  label: string;
  value: number;
}

export interface EngagementPrediction {
  model_id: string;
  model_name: ModelName;
  model_label: string;
  target: string;
  target_formula: string;
  target_unit: string;
  predicted_engagement_rate: number;
  typical_error: number;
  band_low: number;
  band_high: number;
  inputs_used: Record<string, string | number>;
  warnings: string[];
  base_value: number | null;
  contributions: Contribution[] | null;
  contribution_note: string;
  historical: {
    training_mean: number;
    training_median: number;
    matching_groups: GroupObservation[];
  };
  disclaimer: string;
}

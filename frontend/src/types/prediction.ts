export interface ForecastPoint {
  observed_at: string;
  views: number | null;
  predicted: number | null;
  lower: number | null;
  upper: number | null;
}

export interface HorizonForecast {
  label: string;
  hours: number;
  target_at: string;
  supported: boolean;
  predicted_views: number | null;
  added_views: number | null;
  growth_percent: number | null;
  note: string;
}

export interface ModelMetric {
  name: "holt_linear" | "naive_last_value";
  label: string;
  mae: number | null;
  growth_wape: number | null;
  pairs: number;
  available: boolean;
  note: string;
}

export interface PredictionResult {
  eligible: boolean;
  status: "forecast" | "insufficient_data";
  message: string;
  target: string | null;
  method: string | null;
  model_label?: string | null;
  selection?: "evaluated" | "provisional" | null;
  selection_reason?: string | null;
  horizon_label: string | null;
  horizon_steps: number | null;
  cadence_days: number | null;
  resample_step_hours?: number | null;
  trained: boolean;
  observations_used?: number | null;
  train_points: number | null;
  test_points: number | null;
  evaluation_origins?: number | null;
  holdout_start: string | null;
  latest_observed_at?: string | null;
  latest_views?: number | null;
  baseline_mae: number | null;
  model_mae: number | null;
  metrics?: ModelMetric[];
  horizons?: HorizonForecast[];
  warnings?: string[];
  model_version: string;
  generated_at: string | null;
  series: ForecastPoint[];
  limitations: string;
}

export interface ViewObservation {
  observed_at: string;
  views: number;
  source: "analysis" | "csv" | "snapshot";
}

export interface TrackedVideo {
  video_id: string;
  title: string;
  channel_title: string;
  thumbnail_url: string | null;
  latest_analysis_id: string;
  analyses: number;
  observations: number;
  latest_observed_at: string | null;
  latest_views: number | null;
}

export interface TrackedVideoList {
  count: number;
  videos: TrackedVideo[];
}

export interface VideoForecastResponse {
  video_id: string;
  title: string;
  channel_title: string;
  latest_analysis_id: string;
  observations: ViewObservation[];
  prediction: PredictionResult;
  guidance: string;
}

export interface ObservationImportResult {
  video_id: string;
  rows_read: number;
  inserted: number;
  skipped_existing: number;
  warnings: string[];
  forecast: VideoForecastResponse;
}

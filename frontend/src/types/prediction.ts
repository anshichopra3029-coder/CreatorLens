export interface ForecastPoint {
  observed_at: string;
  views: number | null;
  predicted: number | null;
  lower: number | null;
  upper: number | null;
}

export interface PredictionResult {
  eligible: boolean;
  status: "forecast" | "insufficient_data";
  message: string;
  target: string | null;
  method: string | null;
  horizon_label: string | null;
  horizon_steps: number | null;
  cadence_days: number | null;
  trained: boolean;
  train_points: number | null;
  test_points: number | null;
  holdout_start: string | null;
  baseline_mae: number | null;
  model_mae: number | null;
  model_version: string;
  generated_at: string | null;
  series: ForecastPoint[];
  limitations: string;
}

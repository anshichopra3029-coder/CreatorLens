import type { DiagnosisEvidence, PerformanceDiagnosis } from "./diagnosis.ts";
import type { PredictionResult } from "./prediction.ts";

export interface AnalyticsObservation {
  video_id: string;
  title: string;
  observed_at: string | null;
  views: number | null;
  likes: number | null;
  comments: number | null;
  shares: number | null;
  impressions: number | null;
  click_through_rate: number | null;
  watch_time_minutes: number | null;
  average_view_duration_seconds: number | null;
  subscribers_gained: number | null;
}

export interface VideoRollup {
  video_id: string;
  title: string;
  observations: number;
  latest_date: string | null;
  views: number | null;
  likes: number | null;
  comments: number | null;
  shares: number | null;
  impressions: number | null;
  click_through_rate: number | null;
  watch_time_minutes: number | null;
  average_view_duration_seconds: number | null;
  subscribers_gained: number | null;
  engagement_rate: number | null;
  engagement_formula: string;
}

export interface AnalyticsSummary {
  video_count: number;
  observation_count: number;
  total_latest_views: number | null;
  average_engagement_rate: number | null;
  engagement_formula: string;
  formula_note: string;
  videos: VideoRollup[];
}

export interface AnalyticsNarrative {
  executive_summary: string;
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
  content_ideas: string[];
  next_actions: string[];
  additional_data: string;
  limitations: string;
}

export interface AnalyticsPreview {
  filename: string;
  row_count: number;
  video_count: number;
  columns: string[];
  warnings: string[];
  preview: AnalyticsObservation[];
  forecast_ready: boolean;
  forecast_message: string;
  is_demo: false;
}

export interface AnalyticsAnalysis {
  id: string;
  created_at: string;
  source: "analytics_csv";
  filename: string;
  summary: AnalyticsSummary;
  observations: AnalyticsObservation[];
  warnings: string[];
  prediction: PredictionResult;
  narrative_status: "generated" | "unavailable";
  narrative_message: string;
  narrative: AnalyticsNarrative | null;
  diagnosis_status: "generated" | "calculated" | "unavailable";
  diagnosis_message: string;
  diagnosis: PerformanceDiagnosis | null;
  diagnosis_evidence: DiagnosisEvidence | null;
  model: string | null;
  file_saved: true;
  is_demo: false;
}

export interface AnalyticsListItem {
  id: string;
  filename: string;
  created_at: string;
  video_count: number;
  observation_count: number;
  total_latest_views: number | null;
  average_engagement_rate: number | null;
  prediction_eligible: boolean;
  prediction_message: string;
  file_saved: true;
}

export interface AnalyticsListResponse {
  count: number;
  analyses: AnalyticsListItem[];
}

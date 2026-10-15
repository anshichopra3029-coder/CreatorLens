export type DocumentFormat = "csv" | "pdf" | "docx";
export type DocumentStatus = "analyzed" | "extracted" | "unreadable";
export type NarrativeStatus = "generated" | "unavailable" | "not_requested";

export interface ColumnProfile {
  name: string;
  kind: "number" | "text" | "datetime";
  non_empty_count: number;
  missing_count: number;
  numeric_min: number | null;
  numeric_max: number | null;
  numeric_mean: number | null;
  numeric_median: number | null;
}

export interface CategoryStat {
  name: string;
  count: number;
  avg_engagement_rate: number | null;
  total_interactions: number | null;
}

export interface TrendStat {
  period: string;
  label: string;
  count: number;
  avg_engagement_rate: number | null;
  total_interactions: number | null;
}

export interface AnomalyStat {
  row_number: number;
  column: string;
  value: number;
  reason: string;
}

export interface CsvProfile {
  row_count: number;
  column_count: number;
  columns: ColumnProfile[];
  engagement_available: boolean;
  metric_name: string | null;
  metric_formula: string | null;
  metric_note: string | null;
  posts_analyzed: number | null;
  avg_engagement_rate: number | null;
  total_interactions: number | null;
  best_category: string | null;
  categories: CategoryStat[];
  trends: TrendStat[];
  anomalies: AnomalyStat[];
  sample_rows: Record<string, string>[];
}

export interface QuestionRecord {
  id: string;
  question: string;
  answer: string;
  cited_evidence: string;
  uncertainty_note: string;
  created_at: string;
}

export interface DocumentAnalysis {
  id: string;
  filename: string;
  format: DocumentFormat;
  size_bytes: number;
  created_at: string;
  status: DocumentStatus;
  file_saved: true;
  analysis_performed: boolean;
  is_demo: false;
  narrative_status: NarrativeStatus;
  narrative_message: string;
  subject: string | null;
  summary: string | null;
  main_points: string[];
  key_findings: string[];
  facts: string[];
  dates: string[];
  entities: string[];
  risks: string[];
  recommendations: string[];
  text_preview: string;
  csv_profile: CsvProfile | null;
  questions: QuestionRecord[];
  model: string | null;
}

export interface DocumentListItem {
  id: string;
  filename: string;
  format: DocumentFormat;
  size_bytes: number;
  created_at: string;
  status: DocumentStatus;
  file_saved: true;
  analysis_performed: boolean;
  summary: string | null;
}

export interface DocumentListResponse {
  count: number;
  documents: DocumentListItem[];
}

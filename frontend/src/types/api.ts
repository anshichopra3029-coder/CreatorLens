export interface AppliedFilters {
  category: string | null;
  platform: string | null;
  start_date: string | null;
  end_date: string | null;
}

export interface HealthResponse {
  status: string;
  service: string;
}

export interface DashboardSummary {
  is_demo: boolean;
  data_source: string;
  metric_name: string;
  metric_formula: string;
  metric_note: string;
  posts_analyzed: number;
  avg_engagement_rate: number | null;
  total_interactions: number;
  best_category: string | null;
  applied_filters: AppliedFilters;
}

export interface TrendPoint {
  period: string;
  label: string;
  avg_engagement_rate: number | null;
  post_count: number;
  total_interactions: number;
}

export interface TrendsResponse {
  is_demo: boolean;
  data_source: string;
  metric_name: string;
  metric_formula: string;
  points: TrendPoint[];
  applied_filters: AppliedFilters;
}

export interface GroupMetric {
  name: string;
  post_count: number;
  avg_engagement_rate: number | null;
  total_interactions: number;
  avg_views: number | null;
}

export interface ContentComparisonResponse {
  is_demo: boolean;
  data_source: string;
  metric_name: string;
  metric_formula: string;
  categories: GroupMetric[];
  platforms: GroupMetric[];
  applied_filters: AppliedFilters;
}

export interface PostRecord {
  post_id: string;
  title: string;
  platform: string;
  category: string;
  post_datetime: string;
  views: number;
  likes: number;
  comments: number;
  shares: number;
  followers_gained: number;
  engagement_rate: number | null;
}

export interface PostsResponse {
  is_demo: boolean;
  data_source: string;
  metric_name: string;
  metric_formula: string;
  count: number;
  posts: PostRecord[];
  applied_filters: AppliedFilters;
}

export interface InsightCard {
  id: string;
  title: string;
  summary: string;
  evidence: string;
}

export interface InsightsResponse {
  is_demo: boolean;
  data_source: string;
  disclaimer: string;
  metric_name: string;
  metric_formula: string;
  cards: InsightCard[];
}

export interface UploadResponse {
  filename: string;
  size_bytes: number;
  row_count: number;
  column_names: string[];
  expected_columns: {
    present: string[];
    missing: string[];
  };
  validation_message: string;
  warnings: string[];
  is_demo: boolean;
  data_source: string;
  analysis_performed: boolean;
  file_saved: boolean;
}

export interface DemoFilters {
  category?: string;
  platform?: string;
  startDate?: string;
  endDate?: string;
}

export type TimeRange = "all" | "30" | "90";

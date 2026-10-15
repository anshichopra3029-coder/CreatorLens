export interface PublicStatistics {
  views: number | null;
  likes: number | null;
  comments: number | null;
  views_available: boolean;
  likes_available: boolean;
  comments_available: boolean;
  engagement_rate: number | null;
  engagement_formula: string;
  engagement_note: string;
}

export interface VideoMetadata {
  video_id: string;
  url: string;
  title: string;
  description: string;
  channel_title: string;
  thumbnail_url: string | null;
  published_at: string | null;
  duration_seconds: number | null;
  privacy_status: string;
}

export interface TranscriptStatus {
  available: boolean;
  text: string;
  reason: string;
}

export interface AnalyticsAvailability {
  connected: boolean;
  impressions: number | null;
  click_through_rate: number | null;
  audience_retention: number[] | null;
  reason: string;
}

export interface CommentSnippet {
  author: string;
  text: string;
  like_count: number | null;
}

export interface EvidencePoint {
  claim: string;
  evidence: string;
  source: "transcript" | "metadata" | "comments" | "statistics";
}

export interface YoutubeNarrative {
  executive_summary: string;
  intended_audience: string;
  main_topic: string;
  subtopics: string[];
  key_takeaways: string[];
  hook_assessment: string;
  hook_evidence: EvidencePoint[];
  structure_notes: string[];
  title_assessment: string;
  description_assessment: string;
  cta_assessment: string;
  strengths: EvidencePoint[];
  weaknesses: EvidencePoint[];
  recommendations: EvidencePoint[];
  suggested_titles: string[];
  thumbnail_concepts: string[];
  suggested_description: string;
  content_ideas: string[];
  limitations: string;
}

export interface YoutubePreview {
  metadata: VideoMetadata;
  statistics: PublicStatistics;
  transcript: TranscriptStatus;
  analytics: AnalyticsAvailability;
  cached: boolean;
  is_demo: false;
}

export interface YoutubeAnalysis {
  id: string;
  created_at: string;
  metadata: VideoMetadata;
  statistics: PublicStatistics;
  transcript: TranscriptStatus;
  analytics: AnalyticsAvailability;
  comments_status: "available" | "disabled" | "unavailable";
  comments: CommentSnippet[];
  narrative_status: "generated" | "unavailable";
  narrative_message: string;
  narrative: YoutubeNarrative | null;
  model: string | null;
  cached_metadata: boolean;
  file_saved: true;
  is_demo: false;
}

export interface YoutubeListItem {
  id: string;
  video_id: string;
  title: string;
  channel_title: string;
  thumbnail_url: string | null;
  created_at: string;
  views: number | null;
  likes: number | null;
  comments: number | null;
  engagement_rate: number | null;
  file_saved: true;
}

export interface YoutubeListResponse {
  count: number;
  analyses: YoutubeListItem[];
}

export interface OauthStatus {
  connected: boolean;
  oauth_client_configured: boolean;
  impressions: null;
  click_through_rate: null;
  audience_retention: null;
  reason: string;
}

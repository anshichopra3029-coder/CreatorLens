export type EvidenceLevel = "Limited evidence" | "Moderate evidence" | "Stronger evidence";

export interface DiagnosisEvidence {
  subject_id: string;
  title: string;
  scenario: "single_snapshot" | "historical_snapshots" | "multi_video";
  views: number | null;
  likes: number | null;
  comments: number | null;
  shares: number | null;
  include_shares: boolean;
  engagement_rate: number | null;
  engagement_formula: string;
  like_rate: number | null;
  comment_rate: number | null;
  views_per_day: number | null;
  peer_sample_size: number;
  dated_view_points: number;
  baseline_rate: number | null;
  baseline_label: string;
  observations: string[];
  unanswered: string[];
  evidence_level: EvidenceLevel;
  evidence_reasons: string[];
  limitations: string[];
}

export type ClaimKind = "observed" | "inference" | "hypothesis";

export interface StrengthInsight {
  title: string;
  explanation: string;
  evidence: string;
  baseline: string;
  claim_kind: ClaimKind;
}

export interface ImprovementInsight {
  title: string;
  explanation: string;
  evidence: string;
  possible_causes: string[];
  claim_kind: ClaimKind;
}

export interface ReasonItem {
  statement: string;
  evidence: string;
  claim_kind: "hypothesis";
}

export interface ActionItem {
  priority: "High" | "Medium" | "Low";
  action: string;
  reason: string;
  evidence: string;
  success_measure: string;
}

export interface PerformanceDiagnosis {
  summary: string;
  strengths: StrengthInsight[];
  improvements: ImprovementInsight[];
  actions: ActionItem[];
  reasons: ReasonItem[];
  source: "evidence_rules" | "gemini";
  evidence_quality: {
    level: EvidenceLevel;
    reasons: string[];
    limitations: string[];
  };
}

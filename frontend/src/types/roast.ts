export type RoastStyle = "friendly" | "savage" | "brutal";
export type RoastClaimKind = "observed" | "inference" | "hypothesis";

export interface CourtClue {
  label: string;
  detail: string;
  source: string;
  claim_kind: "observed";
}

export interface CourtPoint {
  title: string;
  detail: string;
  evidence: string;
  claim_kind: RoastClaimKind;
}

export interface CourtVerdict {
  summary: string;
  confidence: "Low confidence" | "Moderate confidence" | "Higher confidence";
  why: string;
  missing: string[];
}

export interface NextMove {
  change: string;
  why: string;
  metric: string;
}

export interface FixPack {
  titles: string[];
  thumbnail_concepts: string[];
  hooks: string[];
  note: string;
}

export interface ChallengeReply {
  question: string;
  context: string;
  reply: string;
  defended_original: false;
}

export interface VideoRoast {
  style: RoastStyle;
  take: number;
  opening: string;
  bits?: string[];
  closer?: string;
  observation: string;
  limits: string;
  bridge: string;
  investigation: string[];
  clues: CourtClue[];
  defence: CourtPoint[];
  suspects: CourtPoint[];
  verdict: CourtVerdict;
  next_move: NextMove;
  fixes: FixPack | null;
  challenge: ChallengeReply | null;
  source: "evidence_rules" | "gemini";
}

export interface ContentExperiment {
  id: string;
  video_id: string;
  issue: string;
  proposed_change: string;
  metric: string;
  created_at: string;
  outcome_note: string;
  follow_up_views: number | null;
  completed_task: boolean;
  improvement_shown: false;
  result_note: string;
}

export interface PublicUser {
  id: string;
  email: string;
  display_name: string;
  email_verified: boolean;
  created_at: string;
}

export interface SessionResponse {
  authenticated: boolean;
  verified: boolean;
  csrf_token: string;
  user: PublicUser | null;
}

export interface RecentActivity {
  id: string;
  kind: "youtube" | "document" | "analytics" | string;
  title: string;
  created_at: string;
}

export interface ProfileResponse {
  user: PublicUser;
  videos_analyzed: number;
  diagnoses_saved: number;
  experiments_saved: number;
  documents_saved: number;
  recent: RecentActivity[];
}

export type AnalysisListItem = {
  run_id: string;
  status: string;
  provider: string;
  model: string;
  overall_score: number;
  job_title: string;
  company: string;
  resume_file_name: string;
  created_at: string;
  completed_at?: string | null;
};

export type DashboardSummary = {
  total_runs: number;
  completed_runs: number;
  failed_runs: number;
  average_match_score: number;
  common_skill_gaps: Array<{ skill: string; count: number }>;
  provider_usage: Array<{ provider: string; runs: number }>;
  recent_analyses: AnalysisListItem[];
  tracker_status_counts: Record<string, number>;
  score_history: Array<{
    run_id: string;
    score: number;
    role: string;
    company: string;
    resume_file_name: string;
    created_at: string;
  }>;
  resume_versions: Array<{
    role: string;
    company: string;
    resume_file_name: string;
    latest_resume_file_name: string;
    previous_resume_file_name: string;
    runs: number;
    latest_score: number;
    best_score: number;
    change: number | null;
    latest_run_id: string;
  }>;
  upcoming_actions: Array<{
    run_id: string;
    role: string;
    company: string;
    follow_up_date: string;
    status: string;
  }>;
};

export type ProviderInfo = {
  name: string;
  models: string[];
  default_model: string;
};

export type TrackerItem = {
  run_id: string;
  role: string;
  company: string;
  location: string;
  job_link: string;
  match_score: number;
  tracker_status: string;
  notes: string;
  priority: string;
  applied_at: string;
  follow_up_date: string;
  updated_at: string;
  top_fixes: string[];
  analysis_url: string;
  created_at: string;
};

export type AnalysisResponse = {
  run_id: string;
  status: string;
  provider: string;
  model: string;
  overall_score: number;
  analysis: Record<string, any>;
};

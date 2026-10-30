export const API_URL = process.env.NEXT_PUBLIC_TRUTHFIT_API_URL ?? "http://127.0.0.1:8000";

export type AnalysisListItem = {
  run_id: string;
  status: string;
  provider: string;
  model: string;
  overall_score: number;
  job_title: string;
  company: string;
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

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    cache: "no-store",
  });

  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.detail ?? `API request failed with ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export async function getDashboardSummary(): Promise<DashboardSummary> {
  return apiFetch<DashboardSummary>("/dashboard/summary");
}

export async function getAnalysis(runId: string): Promise<AnalysisResponse> {
  return apiFetch<AnalysisResponse>(`/analysis/${runId}`);
}

export async function getProviders(): Promise<{ providers: ProviderInfo[] }> {
  return apiFetch<{ providers: ProviderInfo[] }>("/providers");
}

export async function getTrackedJobs(): Promise<{ jobs: TrackerItem[] }> {
  return apiFetch<{ jobs: TrackerItem[] }>("/tracker");
}

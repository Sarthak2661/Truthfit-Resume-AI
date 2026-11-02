import "server-only";

import { API_URL } from "./api-config";
import type {
  AnalysisResponse,
  DashboardSummary,
  ProviderInfo,
  TrackerItem,
} from "./api-types";
import { createClient } from "./supabase/server";

export type { AnalysisListItem, ProviderInfo } from "./api-types";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const supabase = await createClient();
  const { data, error } = await supabase.auth.getSession();
  const accessToken = data.session?.access_token;
  if (error || !accessToken) {
    throw new Error("Authentication is required.");
  }

  const headers = new Headers(init?.headers);
  headers.set("authorization", `Bearer ${accessToken}`);
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers,
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

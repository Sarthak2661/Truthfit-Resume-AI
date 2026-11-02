"use client";

import { API_URL } from "./api-config";
import { createClient } from "./supabase/client";

export async function authenticatedFetch(path: string, init?: RequestInit): Promise<Response> {
  const supabase = createClient();
  const { data, error } = await supabase.auth.getSession();
  const accessToken = data.session?.access_token;

  if (error || !accessToken) {
    throw new Error("Your session has expired. Sign in again to continue.");
  }

  const headers = new Headers(init?.headers);
  headers.set("authorization", `Bearer ${accessToken}`);

  return fetch(`${API_URL}${path}`, { ...init, headers });
}

"use client";

import { useEffect, useState } from "react";
import { authenticatedFetch } from "../lib/authenticated-fetch";
import { createClient } from "../lib/supabase/client";

type AccountData = {
  analyses: number;
  resumes: number;
  jobs: number;
  retained_originals: number;
  oldest_record: string | null;
  retention_days: number;
  daily_analyses_used: number;
  daily_analysis_limit: number;
};

export function AccountDataControls() {
  const [data, setData] = useState<AccountData | null>(null);
  const [error, setError] = useState("");
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    void loadData();
  }, []);

  async function loadData() {
    try {
      const response = await authenticatedFetch("/account/data");
      if (!response.ok) throw new Error("Could not load stored-data details.");
      setData(await response.json());
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Could not load stored-data details.");
    }
  }

  async function deleteAllData() {
    const confirmed = window.confirm(
      "Delete all TruthFit analyses, resumes, jobs, evidence, and tracker data? This cannot be undone.",
    );
    if (!confirmed) return;

    setDeleting(true);
    setError("");
    try {
      const response = await authenticatedFetch("/account/data", { method: "DELETE" });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail ?? "Could not delete account data.");
      }
      await createClient().auth.signOut();
      window.location.assign("/login");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Could not delete account data.");
      setDeleting(false);
    }
  }

  return (
    <div className="card privacy-data-card">
      <span className="section-label">Stored data</span>
      <h2>Privacy and retention</h2>
      <p className="muted">
        Original resumes are discarded by default. Completed analyses expire after {data?.retention_days ?? "the configured"} days.
      </p>
      {data ? (
        <div className="privacy-data-grid">
          <DataPoint label="Analyses" value={data.analyses} />
          <DataPoint label="Resumes" value={data.resumes} />
          <DataPoint label="Jobs" value={data.jobs} />
          <DataPoint label="Encrypted originals" value={data.retained_originals} />
          <DataPoint label="Analyses used today" value={`${data.daily_analyses_used} / ${data.daily_analysis_limit}`} />
        </div>
      ) : null}
      {data?.oldest_record ? <p className="muted">Oldest stored analysis: {new Date(data.oldest_record).toLocaleDateString()}</p> : null}
      {error ? <div className="alert">{error}</div> : null}
      <button className="button danger" disabled={deleting} onClick={deleteAllData} type="button">
        {deleting ? "Deleting data..." : "Delete all TruthFit data"}
      </button>
      <p className="muted">This removes TruthFit application data and signs you out. It does not delete your Supabase login identity.</p>
    </div>
  );
}

function DataPoint({ label, value }: { label: string; value: number | string }) {
  return <div><strong>{value}</strong><span>{label}</span></div>;
}

"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { authenticatedFetch } from "../lib/authenticated-fetch";

type AnalysisRunStatusProps = {
  runId: string;
  initialStatus: string;
  initialError?: string;
};

export function AnalysisRunStatus({ runId, initialStatus, initialError = "" }: AnalysisRunStatusProps) {
  const router = useRouter();
  const [status, setStatus] = useState(initialStatus);
  const [error, setError] = useState(initialError);

  useEffect(() => {
    if (status === "completed" || status === "failed") {
      return;
    }

    const poll = async () => {
      try {
        const response = await authenticatedFetch(`/analysis/${runId}`);
        if (!response.ok) {
          throw new Error("Could not check the analysis status.");
        }
        const run = await response.json();
        setStatus(run.status);
        if (run.status === "completed") {
          router.refresh();
        } else if (run.status === "failed") {
          setError(run.analysis?.error?.message ?? "The analysis could not be completed.");
        }
      } catch (pollError) {
        setError(pollError instanceof Error ? pollError.message : "Could not check the analysis status.");
      }
    };

    const timer = window.setInterval(poll, 1800);
    void poll();
    return () => window.clearInterval(timer);
  }, [router, runId, status]);

  const isFailed = status === "failed";
  return (
    <main className="page narrow-page">
      <section className="card run-status-card" aria-live="polite">
        <span className="section-label">Fit review</span>
        <h1>{isFailed ? "Analysis could not finish" : "Reviewing your evidence"}</h1>
        <p className="muted">
          {isFailed
            ? error
            : "TruthFit is comparing the resume with the role requirements. You can leave this page and return from the dashboard."}
        </p>
        {!isFailed ? <div className="run-status-progress" aria-hidden="true"><span /></div> : null}
        <div className="button-row">
          {isFailed ? <Link className="button" href="/jobs">Try another review</Link> : null}
          <Link className="button secondary" href="/dashboard">Open dashboard</Link>
        </div>
      </section>
    </main>
  );
}

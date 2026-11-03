import Link from "next/link";
import type { CSSProperties } from "react";

import { ErrorPanel } from "../../components/ErrorPanel";
import { ScoreCard } from "../../components/ScoreCard";
import { getDashboardSummary } from "../../lib/api";

const pipelineStages = ["Saved", "Applied", "Interview", "Rejected"];

export default async function DashboardPage({ searchParams }: { searchParams: Promise<{ confirmed?: string }> }) {
  try {
    const query = await searchParams;
    const summary = await getDashboardSummary();
    const counts = summary.tracker_status_counts ?? {};
    const tracked = pipelineStages.reduce((total, stage) => total + Number(counts[stage] ?? 0), 0);
    const active = Math.max(0, tracked - Number(counts.Rejected ?? 0));
    const maxGapCount = Math.max(1, ...summary.common_skill_gaps.map((item) => item.count));

    return (
      <section className="section">
        {query.confirmed === "1" ? <div className="success">Email confirmed. Your account is ready.</div> : null}
        <div className="page-heading-row">
          <div>
            <div className="section-label">Job search dashboard</div>
            <h1>Your application workspace</h1>
            <p className="muted">Track fit reviews, application progress, recurring gaps, and the next action to take.</p>
          </div>
          <Link className="button" href="/jobs">Analyze a role</Link>
        </div>

        <div className="section grid four dashboard-kpis">
          <ScoreCard label="Active opportunities" value={active} detail={`${tracked} tracked roles`} />
          <ScoreCard label="Applied" value={counts.Applied ?? 0} detail="applications sent" />
          <ScoreCard label="Interviews" value={counts.Interview ?? 0} detail="in progress" />
          <ScoreCard label="Average match" value={`${summary.average_match_score}/100`} detail={`${summary.completed_runs} completed reviews`} />
        </div>

        <div className="section grid dashboard-primary-grid">
          <div className="card">
            <div className="card-heading-row">
              <div>
                <span className="section-label">Application pipeline</span>
                <h3>Where your opportunities stand</h3>
              </div>
              <Link className="text-link" href="/tracker">Open tracker</Link>
            </div>
            <div className="pipeline-summary" aria-label="Application pipeline">
              {pipelineStages.map((stage) => (
                <div className={`pipeline-stage pipeline-${stage.toLowerCase()}`} key={stage}>
                  <strong>{counts[stage] ?? 0}</strong>
                  <span>{stage}</span>
                </div>
              ))}
            </div>
            {!tracked ? <p className="muted empty-copy">Save a reviewed role to start your application pipeline.</p> : null}
          </div>

          <div className="card">
            <span className="section-label">Score history</span>
            <h3>Recent fit reviews</h3>
            <div className="score-history" aria-label="Recent match scores">
              {summary.score_history.map((item) => (
                <Link className="score-history-item" href={`/analysis/${item.run_id}`} key={item.run_id} title={`${item.role}: ${item.score}/100`}>
                  <span className="score-history-value">{item.score}</span>
                  <span className="score-history-track">
                    <span style={{ "--value": `${item.score}%` } as CSSProperties} />
                  </span>
                  <span className="score-history-label">{item.role}</span>
                </Link>
              ))}
              {!summary.score_history.length ? <p className="muted">Score history appears after your first completed review.</p> : null}
            </div>
          </div>
        </div>

        <div className="section grid two dashboard-detail-grid">
          <div className="card">
            <div className="card-heading-row">
              <div>
                <span className="section-label">Recent activity</span>
                <h3>Latest fit reviews</h3>
              </div>
            </div>
            <div className="table-scroll">
              <table className="table compact-table">
                <thead><tr><th>Role</th><th>Resume</th><th>Match</th><th>Open</th></tr></thead>
                <tbody>
                  {summary.recent_analyses.map((run) => (
                    <tr key={run.run_id}>
                      <td><strong>{run.job_title || "Untitled role"}</strong><br /><span className="muted">{run.company || "Company not specified"}</span></td>
                      <td className="muted">{run.resume_file_name || "Resume"}</td>
                      <td><span className={`status ${run.overall_score >= 75 ? "good" : run.overall_score >= 55 ? "warn" : "bad"}`}>{run.overall_score}/100</span></td>
                      <td><Link className="text-link" href={`/analysis/${run.run_id}`}>View</Link></td>
                    </tr>
                  ))}
                  {!summary.recent_analyses.length ? <tr><td colSpan={4} className="muted">No analyses yet.</td></tr> : null}
                </tbody>
              </table>
            </div>
          </div>

          <div className="grid dashboard-side-stack">
            <div className="card">
              <span className="section-label">Recurring gaps</span>
              <h3>Skills to strengthen</h3>
              <div className="gap-bars">
                {summary.common_skill_gaps.slice(0, 5).map((gap) => (
                  <div className="gap-row" key={gap.skill}>
                    <div><strong>{gap.skill}</strong><span>{gap.count} review{gap.count === 1 ? "" : "s"}</span></div>
                    <span className="gap-track"><span style={{ "--value": `${(gap.count / maxGapCount) * 100}%` } as CSSProperties} /></span>
                  </div>
                ))}
                {!summary.common_skill_gaps.length ? <p className="muted">Recurring gaps appear after multiple reviews.</p> : null}
              </div>
            </div>

            <div className="card">
              <span className="section-label">Upcoming actions</span>
              <h3>Follow-ups</h3>
              <div className="action-list">
                {summary.upcoming_actions.map((item) => (
                  <Link href={`/analysis/${item.run_id}`} key={item.run_id}>
                    <strong>{item.role}</strong>
                    <span>{item.company} · {formatDate(item.follow_up_date)}</span>
                  </Link>
                ))}
                {!summary.upcoming_actions.length ? <p className="muted">Add a follow-up date in the tracker to see it here.</p> : null}
              </div>
            </div>
          </div>
        </div>

        <div className="section card">
          <div className="card-heading-row">
            <div><span className="section-label">Resume versions</span><h3>Compare recent performance</h3></div>
            <span className="muted">Scores vary by job description; use changes as directional evidence.</span>
          </div>
          <div className="version-grid">
            {summary.resume_versions.map((version) => (
              <Link className="version-card" href={`/analysis/${version.latest_run_id}`} key={`${version.company}-${version.role}`}>
                <span className="section-label">{version.company}</span>
                <strong>{version.role}</strong>
                <span>{version.latest_resume_file_name} · {version.runs} review{version.runs === 1 ? "" : "s"}</span>
                <div><b>{version.latest_score}</b><small>latest</small><b>{version.best_score}</b><small>best</small></div>
                <span className={version.change == null ? "muted" : version.change >= 0 ? "positive-text" : "negative-text"}>
                  {version.change == null
                    ? "First measured version"
                    : `${version.change >= 0 ? "+" : ""}${version.change} vs ${version.previous_resume_file_name || "previous resume"}`}
                </span>
              </Link>
            ))}
            {!summary.resume_versions.length ? <p className="muted">Resume comparisons appear after completed reviews.</p> : null}
          </div>
        </div>
      </section>
    );
  } catch (error) {
    return <ErrorPanel message={error instanceof Error ? error.message : "Unknown API error"} />;
  }
}

function formatDate(value: string): string {
  const date = new Date(`${value}T00:00:00`);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString("en", { month: "short", day: "numeric" });
}

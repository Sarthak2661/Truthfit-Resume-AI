import Link from "next/link";
import { ErrorPanel } from "../../components/ErrorPanel";
import { ScoreCard } from "../../components/ScoreCard";
import { getDashboardSummary } from "../../lib/api";

export default async function DashboardPage() {
  try {
    const summary = await getDashboardSummary();

    return (
      <section className="section">
        <div className="section-label">Operations dashboard</div>
        <h1>Analysis workspace</h1>
        <p className="muted">Recent runs, match quality, recurring skill gaps, provider usage, and failures.</p>

        <div className="section grid five">
          <ScoreCard label="Total runs" value={summary.total_runs} detail="all analyses" />
          <ScoreCard label="Completed" value={summary.completed_runs} detail="stored results" />
          <ScoreCard label="Average score" value={summary.average_match_score} detail="completed runs" />
          <ScoreCard label="Providers" value={summary.provider_usage.length} detail="used so far" />
          <ScoreCard label="Failed runs" value={summary.failed_runs} detail="needs review" />
        </div>

        <div className="section grid two">
          <div className="card">
            <h3>Recent analyses</h3>
            <table className="table">
              <thead>
                <tr>
                  <th>Role</th>
                  <th>Score</th>
                  <th>Status</th>
                  <th>Open</th>
                </tr>
              </thead>
              <tbody>
                {summary.recent_analyses.length ? (
                  summary.recent_analyses.map((run) => (
                    <tr key={run.run_id}>
                      <td>
                        <strong>{run.job_title || "Untitled role"}</strong>
                        <br />
                        <span className="muted">{run.company || run.provider}</span>
                      </td>
                      <td>{run.overall_score}/100</td>
                      <td>
                        <span className={`status ${run.status === "completed" ? "good" : run.status === "failed" ? "bad" : "warn"}`}>
                          {run.status}
                        </span>
                      </td>
                      <td>
                        <Link className="pill" href={`/analysis/${run.run_id}`}>
                          View
                        </Link>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={4} className="muted">
                      No analyses yet. Start from the Jobs page.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          <div className="grid">
            <div className="card">
              <h3>Common skill gaps</h3>
              {summary.common_skill_gaps.length ? (
                summary.common_skill_gaps.map((gap) => (
                  <p key={gap.skill}>
                    <strong>{gap.skill}</strong> <span className="muted">seen in {gap.count} run(s)</span>
                  </p>
                ))
              ) : (
                <p className="muted">No recurring gaps yet.</p>
              )}
            </div>
            <div className="card">
              <h3>Provider usage</h3>
              {summary.provider_usage.length ? (
                summary.provider_usage.map((item) => (
                  <p key={item.provider}>
                    <strong>{item.provider}</strong> <span className="muted">{item.runs} run(s)</span>
                  </p>
                ))
              ) : (
                <p className="muted">Provider usage will appear after the first analysis.</p>
              )}
            </div>
          </div>
        </div>
      </section>
    );
  } catch (error) {
    return <ErrorPanel message={error instanceof Error ? error.message : "Unknown API error"} />;
  }
}

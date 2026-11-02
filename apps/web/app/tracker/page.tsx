import { ErrorPanel } from "../../components/ErrorPanel";
import { TrackerBoard } from "../../components/TrackerBoard";
import { getTrackedJobs } from "../../lib/api";

export default async function TrackerPage() {
  try {
    const tracker = await getTrackedJobs();
    return (
      <section className="section">
        <div className="section-label">Job tracker</div>
        <h1>Tracked opportunities</h1>
        <p className="muted">Prioritize roles, update application stages, and keep follow-ups connected to each fit review.</p>
        <TrackerBoard initialJobs={tracker.jobs} />
      </section>
    );
  } catch (error) {
    return <ErrorPanel message={error instanceof Error ? error.message : "Unknown API error"} />;
  }
}

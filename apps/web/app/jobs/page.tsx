import { ErrorPanel } from "../../components/ErrorPanel";
import { getProviders } from "../../lib/api";
import { JobAnalysisClient } from "./JobAnalysisClient";

export default async function JobsPage() {
  try {
    const { providers } = await getProviders();
    return (
      <section className="section">
        <div className="section-label">Analyze</div>
        <h1>Review a resume against a job</h1>
        <p className="muted">
          Upload the resume, add the job description, confirm the role signals, and run the full evidence review from one place.
        </p>
        <div className="section">
          <JobAnalysisClient providers={providers} />
        </div>
      </section>
    );
  } catch (error) {
    return <ErrorPanel message={error instanceof Error ? error.message : "Unknown API error"} />;
  }
}

import { ErrorPanel } from "../../../components/ErrorPanel";
import { ResumeBulletEditor } from "../../../components/ResumeBulletEditor";
import { getAnalysis } from "../../../lib/api";

type PageProps = {
  params: Promise<{ id: string }>;
};

function asList(value: unknown): any[] {
  return Array.isArray(value) ? value : [];
}

function statusClass(value: unknown): string {
  const normalized = String(value ?? "").toLowerCase();
  if (normalized.includes("support") || normalized.includes("high") || normalized.includes("important")) {
    return "good";
  }
  if (normalized.includes("missing") || normalized.includes("risk")) {
    return "bad";
  }
  return "warn";
}

export default async function TailorPage({ params }: PageProps) {
  const { id } = await params;

  try {
    const run = await getAnalysis(id);
    const analysis = run.analysis;
    const bullets = asList(analysis.before_after_bullets);
    const tailored = analysis.tailored_resume_content ?? {};
    const fixes = asList(analysis.resume_fix_suggestions);
    const priorityFixes = asList(analysis.fix_impact_matrix);
    const projects = asList(analysis.project_suggestions);
    const certifications = asList(analysis.certification_suggestions);
    const learningPlan = asList(analysis.skill_gap_learning_plan);
    const coverLetter = String(analysis.cover_letter ?? "");

    return (
      <section className="section">
        <div className="section-label">Resume tailoring</div>
        <h1>What to fix before applying</h1>
        <p className="muted">Suggested rewrites, proof checks, and the next few changes worth making before applying.</p>

        <div className="section card">
          <h3>Tailored summary</h3>
          <p>{tailored.tailored_summary || "No tailored summary returned for this run."}</p>
        </div>

        <div className="section card">
          <h3>What to fix first</h3>
          <table className="table">
            <thead>
              <tr>
                <th>Fix</th>
                <th>Impact</th>
                <th>Effort</th>
                <th>Priority</th>
              </tr>
            </thead>
            <tbody>
              {priorityFixes.slice(0, 5).map((item, index) => (
                <tr key={index}>
                  <td>
                    <strong>{item.fix ?? item.issue ?? "Recommended fix"}</strong>
                    <br />
                    <span className="muted">{item.why_it_matters ?? item.suggested_fix ?? "Improves role alignment."}</span>
                  </td>
                  <td>{item.impact ?? "Medium"}</td>
                  <td>{item.effort ?? "Medium"}</td>
                  <td>
                    <span className={`status ${statusClass(item.priority)}`}>{item.priority ?? "Would help"}</span>
                  </td>
                </tr>
              ))}
              {!priorityFixes.length ? (
                <tr>
                  <td colSpan={4} className="muted">No prioritized fixes returned for this run.</td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>

        <div className="section card">
          <h3>Inline resume editor</h3>
          <p className="muted">Review each rewrite, adjust the wording, and mark what you want to keep before exporting.</p>
          <ResumeBulletEditor bullets={bullets} />
        </div>

        <div className="section grid two">
          {fixes.slice(0, 6).map((item, index) => (
            <div className="card" key={index}>
              <span className="section-label">{item.priority ?? item.impact ?? "Important"}</span>
              <h3>{item.issue ?? item.finding ?? "Resume fix"}</h3>
              <p className="muted">{item.suggested_fix ?? item.recommendation ?? "Improve this section with evidence already present in your profile."}</p>
            </div>
          ))}
        </div>

        <div className="section grid two">
          <div className="card">
            <h3>Project ideas</h3>
            {projects.slice(0, 3).map((item, index) => (
              <p key={index}>
                <span className={`status ${statusClass(item.priority)}`}>{item.priority ?? "Would help"}</span>{" "}
                <strong>{item.project_title ?? "Project idea"}</strong>
                <br />
                <span className="muted">{item.suggested_scope ?? item.why_it_helps ?? "Build proof for a role gap."}</span>
              </p>
            ))}
            {!projects.length ? <p className="muted">No project suggestions returned for this run.</p> : null}
          </div>

          <div className="card">
            <h3>Certifications and learning</h3>
            {certifications.slice(0, 2).map((item, index) => (
              <p key={`cert-${index}`}>
                <span className={`status ${statusClass(item.priority)}`}>{item.priority ?? "Optional"}</span>{" "}
                <strong>{item.certification ?? "Certification"}</strong>
                <br />
                <span className="muted">{item.why_it_helps ?? item.target_gap ?? "Useful for closing a proof gap."}</span>
              </p>
            ))}
            {learningPlan.slice(0, 2).map((item, index) => (
              <p key={`learning-${index}`}>
                <span className={`status ${statusClass(item.priority)}`}>{item.priority ?? "Would help"}</span>{" "}
                <strong>{item.skill ?? "Learning step"}</strong>
                <br />
                <span className="muted">{item.learning_action ?? item.mini_project_idea ?? "Practice this with a small evidence-backed project."}</span>
              </p>
            ))}
            {!certifications.length && !learningPlan.length ? <p className="muted">No certification or learning suggestions returned.</p> : null}
          </div>
        </div>

        {coverLetter ? (
          <div className="section card">
            <h3>Cover letter draft</h3>
            <p className="muted preserve-lines">{coverLetter}</p>
          </div>
        ) : null}
      </section>
    );
  } catch (error) {
    return <ErrorPanel message={error instanceof Error ? error.message : "Unknown API error"} />;
  }
}

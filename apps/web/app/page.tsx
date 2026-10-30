import Link from "next/link";

export default function HomePage() {
  return (
    <>
      <section className="hero">
        <div>
          <div className="eyebrow">Resume review for real job decisions</div>
          <h1>Know what to apply for, what to fix, and what to prove.</h1>
          <p>
            TruthFit compares your resume against a specific job, explains the score, catches weak evidence,
            and turns the review into clear resume improvements.
          </p>
          <div className="hero-actions">
            <Link className="button" href="/jobs">
              Start Review
            </Link>
            <Link className="button secondary hero-secondary" href="/dashboard">
              View Dashboard
            </Link>
          </div>
        </div>

        <div className="product-preview" aria-label="TruthFit analysis preview">
          <div className="preview-header">
            <span className="pill">Evidence-based match</span>
            <strong>78/100</strong>
          </div>
          <div className="score-ring">
            <span>Good Fit</span>
          </div>
          <div className="insight-list">
            <div>
              <span className="dot good-dot" />
              <p>
                <strong>Strong proof</strong>
                Python, SQL, Kafka, dashboards
              </p>
            </div>
            <div>
              <span className="dot warn-dot" />
              <p>
                <strong>Needs evidence</strong>
                Cloud deployment details
              </p>
            </div>
            <div>
              <span className="dot bad-dot" />
              <p>
                <strong>Verify first</strong>
                Eligibility and location fit
              </p>
            </div>
          </div>
          <div className="preview-footer">Personal details redacted before provider analysis.</div>
        </div>
      </section>

      <section className="section grid three">
        <Link className="card" href="/jobs">
          <span className="section-label">Step 1</span>
          <h3>Upload safely</h3>
          <p className="muted">Parse your resume and review a redacted preview before analysis.</p>
        </Link>
        <Link className="card" href="/jobs">
          <span className="section-label">Step 2</span>
          <h3>Compare to a role</h3>
          <p className="muted">Extract hard requirements, preferred skills, and role-specific signals.</p>
        </Link>
        <Link className="card" href="/dashboard">
          <span className="section-label">Step 3</span>
          <h3>Act on the gaps</h3>
          <p className="muted">Review scores, missing proof, rewrite ideas, and saved analysis history.</p>
        </Link>
      </section>
    </>
  );
}

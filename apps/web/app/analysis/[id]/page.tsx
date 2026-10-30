import Link from "next/link";
import type { CSSProperties } from "react";
import { ErrorPanel } from "../../../components/ErrorPanel";
import { ScoreCard } from "../../../components/ScoreCard";
import { TrackerAction } from "../../../components/TrackerAction";
import { getAnalysis } from "../../../lib/api";

type PageProps = {
  params: Promise<{ id: string }>;
};

function asList(value: unknown): any[] {
  return Array.isArray(value) ? value : [];
}

function statusClass(value: unknown): string {
  const normalized = String(value ?? "").toLowerCase();
  if (normalized.includes("strong") || normalized.includes("support") || normalized.includes("covered") || normalized.includes("high")) {
    return "good";
  }
  if (normalized.includes("missing") || normalized.includes("weak") || normalized.includes("risk")) {
    return "bad";
  }
  return "warn";
}

function buildSkillsEvidenceRows(matchedSkills: any[], atsKeywords: any[]): any[] {
  const rows = new Map<string, any>();

  matchedSkills.forEach((item) => {
    const skill = String(item.skill ?? "Matched skill");
    rows.set(skill.toLowerCase(), {
      skill,
      jdSignal: item.jd_signal ?? item.requirement ?? "Matched requirement",
      resumeEvidence: item.resume_evidence ?? "Resume evidence not returned.",
      status: item.evidence_status ?? item.status ?? "Supported",
    });
  });

  atsKeywords.forEach((item) => {
    const skill = String(item.keyword ?? "Keyword");
    const key = skill.toLowerCase();
    const existing = rows.get(key);

    rows.set(key, {
      skill: existing?.skill ?? skill,
      jdSignal: existing?.jdSignal ?? item.jd_signal ?? item.keyword ?? "Keyword match",
      resumeEvidence: existing?.resumeEvidence ?? item.resume_evidence ?? "Not found in resume.",
      status: existing?.status ?? item.coverage_status ?? "Needs proof",
    });
  });

  return Array.from(rows.values());
}

function driverPercent(value: unknown): number {
  return Math.min(Math.abs(Number(value ?? 0)) * 4, 100);
}

function coveragePercentFromStatus(value: unknown): number {
  const status = statusClass(value);
  if (status === "good") {
    return 90;
  }
  if (status === "warn") {
    return 55;
  }
  return 25;
}

function buildApplyReadiness({
  atsFormattingChecks,
  requirementCategories,
  unsupportedClaims,
  topFixes,
  recommendation,
  overallScore,
}: {
  atsFormattingChecks: any[];
  requirementCategories: any[];
  unsupportedClaims: any[];
  topFixes: any[];
  recommendation: unknown;
  overallScore: number;
}) {
  const parserConfidence = parserConfidenceLabel(atsFormattingChecks);
  const requirementCoverage = requirementCoverageLabel(requirementCategories);
  const finalRecommendation = String(recommendation || scoreRecommendation(overallScore, unsupportedClaims.length, topFixes.length));
  const blockingSignals = [
    unsupportedClaims.length ? `${unsupportedClaims.length} unsupported claim(s) need verification` : "",
    parserConfidence === "Needs review" ? "resume formatting needs a manual check" : "",
    parserConfidence === "Unavailable" ? "run a fresh review to include parser checks" : "",
    requirementCoverage === "Needs proof" ? "core requirements need stronger evidence" : "",
  ].filter(Boolean);

  return {
    parserConfidence,
    requirementCoverage,
    parserPercent: parserConfidencePercent(parserConfidence),
    coveragePercent: requirementCoveragePercent(requirementCoverage),
    claimRiskPercent: Math.max(0, 100 - Math.min(unsupportedClaims.length * 25, 100)),
    recommendation: finalRecommendation,
    reason: blockingSignals.length
      ? `${blockingSignals.join(", ")} before applying.`
      : "The main signals are supported well enough to move into tailoring and application tracking.",
  };
}

function parserConfidenceLabel(checks: any[]): string {
  if (!checks.length) {
    return "Unavailable";
  }

  const reviewCount = checks.filter((item) => String(item.status ?? "").toLowerCase() !== "pass").length;
  if (reviewCount === 0) {
    return "High";
  }
  if (reviewCount <= 2) {
    return "Medium";
  }
  return "Needs review";
}

function parserConfidencePercent(label: string): number {
  if (label === "High") {
    return 95;
  }
  if (label === "Medium") {
    return 70;
  }
  if (label === "Needs review") {
    return 35;
  }
  return 0;
}

function requirementCoverageLabel(categories: any[]): string {
  if (!categories.length) {
    return "Not checked";
  }

  const coveredCount = categories.filter((item) => statusClass(item.candidate_status ?? item.status) === "good").length;
  const ratio = coveredCount / categories.length;
  if (ratio >= 0.75) {
    return "Strong";
  }
  if (ratio >= 0.45) {
    return "Partial";
  }
  return "Needs proof";
}

function requirementCoveragePercent(label: string): number {
  if (label === "Strong") {
    return 90;
  }
  if (label === "Partial") {
    return 60;
  }
  if (label === "Needs proof") {
    return 30;
  }
  return 0;
}

function scoreRecommendation(overallScore: number, unsupportedCount: number, fixCount: number): string {
  if (overallScore >= 80 && unsupportedCount === 0) {
    return "Ready to apply";
  }
  if (overallScore >= 65 || fixCount) {
    return "Tailor before applying";
  }
  return "Improve resume first";
}

export default async function AnalysisDetailPage({ params }: PageProps) {
  const { id } = await params;

  try {
    const run = await getAnalysis(id);
    const analysis = run.analysis;
    const scores = analysis.scores ?? {};
    const summary = analysis.match_summary ?? {};
    const skills = analysis.skills_analysis ?? {};
    const job = analysis.job_details ?? {};
    const requirements = analysis.jd_requirements ?? {};
    const scoreDrivers = asList(analysis.score_drivers);
    const matchedSkills = asList(skills.matched_skills);
    const atsKeywords = asList(analysis.ats_keyword_coverage);
    const skillsEvidenceRows = buildSkillsEvidenceRows(matchedSkills, atsKeywords);
    const requirementCategories = asList(requirements.requirement_categories);
    const atsFormattingChecks = asList(analysis.ats_formatting_checks);
    const tracker = analysis.tracker ?? {};
    const unsupportedClaims = asList(analysis.hallucination_guardrail);
    const allFixes = asList(analysis.fix_impact_matrix);
    const topFixes = allFixes.slice(0, 3);
    const additionalFixes = allFixes.slice(3, 6);
    const readiness = buildApplyReadiness({
      atsFormattingChecks,
      requirementCategories,
      unsupportedClaims,
      topFixes,
      recommendation: summary.apply_recommendation,
      overallScore: Number(scores.overall_match_score ?? run.overall_score ?? 0),
    });

    return (
      <section className="section">
        <div className="section-label">Fit review</div>
        <h1>{summary.headline || "Resume analysis"}</h1>
        <p className="muted">{summary.short_explanation || "A practical resume-to-role review with evidence, risks, and next steps."}</p>

        <div className="section grid five">
          <ScoreCard label="Overall match" value={`${scores.overall_match_score ?? run.overall_score}/100`} detail={scores.match_label} />
          <ScoreCard label="Technical match" value={`${scores.technical_match_score ?? 0}/100`} />
          <ScoreCard label="Evidence coverage" value={`${scores.resume_evidence_score ?? 0}/100`} />
          <ScoreCard label="Experience fit" value={`${scores.experience_match_score ?? 0}/100`} />
          <ScoreCard label="Eligibility fit" value={`${scores.eligibility_score ?? 0}/100`} />
        </div>

        <div className="section card readiness-panel">
          <div>
            <span className="section-label">Apply readiness</span>
            <h2>{readiness.recommendation}</h2>
            <p className="muted">{readiness.reason}</p>
          </div>
          <div className="readiness-metrics">
            <div>
              <span>Parser confidence</span>
              <strong>{readiness.parserConfidence}</strong>
              <span className="metric-bar" style={{ "--value": `${readiness.parserPercent}%` } as CSSProperties} />
            </div>
            <div>
              <span>Requirement coverage</span>
              <strong>{readiness.requirementCoverage}</strong>
              <span className="metric-bar" style={{ "--value": `${readiness.coveragePercent}%` } as CSSProperties} />
            </div>
            <div>
              <span>Unsupported claims</span>
              <strong>{unsupportedClaims.length}</strong>
              <span className="metric-bar risk-bar" style={{ "--value": `${readiness.claimRiskPercent}%` } as CSSProperties} />
            </div>
          </div>
          <div className="readiness-fixes">
            <span className="section-label">Top fixes</span>
            {topFixes.length ? (
              topFixes.map((item, index) => (
                <p key={index}>
                  <strong>{item.fix ?? item.recommendation ?? item.issue ?? "Recommended fix"}</strong>
                  <br />
                  <span className="muted">
                    Impact: {item.impact ?? "Important"} · Effort: {item.effort ?? "Medium"}
                  </span>
                </p>
              ))
            ) : (
              <p className="muted">No priority fixes were returned for this run.</p>
            )}
          </div>
        </div>

        <div className="section grid three">
          <div className="card">
            <span className="section-label">Role</span>
            <h3>{job.job_title || "Target role"}</h3>
            <p className="muted">{job.company_name || "Company not specified"}</p>
          </div>
          <div className="card">
            <span className="section-label">Location</span>
            <h3>{job.location_or_work_policy || "Not specified"}</h3>
            <p className="muted">{job.employment_type || job.contract_or_full_time || "Work policy not found"}</p>
          </div>
          <div className="card">
            <span className="section-label">Experience</span>
            <h3>{job.experience_required || "Not specified"}</h3>
            <p className="muted">{job.degree_required || "Education requirement not found"}</p>
          </div>
          <div className="card">
            <span className="section-label">Target region</span>
            <h3>{job.target_region || "US"}</h3>
            <p className="muted">Adjusts review context for location, role language, and eligibility signals.</p>
          </div>
        </div>

        <div className="section grid two">
          <div className="card">
            <h3>Score drivers</h3>
            <div className="bar-list">
              {scoreDrivers.slice(0, 6).map((item, index) => {
                const contribution = Number(item.contribution ?? 0);
                return (
                  <div className="driver-row" key={index}>
                    <div className="driver-copy">
                      <strong>{item.driver ?? "Score driver"}</strong>
                      <span className="muted">{item.evidence ?? "Evidence not returned."}</span>
                    </div>
                    <div className="driver-impact">
                      <span className={`status ${contribution >= 0 ? "good" : "bad"}`}>
                        {contribution >= 0 ? "+" : ""}
                        {contribution}
                      </span>
                      <span
                        className={`driver-bar ${contribution >= 0 ? "positive" : "negative"}`}
                        style={{ "--value": `${driverPercent(contribution)}%` } as CSSProperties}
                      />
                    </div>
                  </div>
                );
              })}
              {!scoreDrivers.length ? <p className="muted">Score drivers were not returned for this run.</p> : null}
            </div>
          </div>

          <div className="card">
            <h3>Requirement coverage</h3>
            <div className="coverage-list">
              {requirementCategories.slice(0, 6).map((item, index) => {
                const status = item.candidate_status ?? item.status ?? "Needs proof";
                return (
                  <div className="coverage-row" key={index}>
                    <div className="coverage-head">
                      <strong>{item.category ?? "Requirement area"}</strong>
                      <span className={`status ${statusClass(status)}`}>{status}</span>
                    </div>
                    <span className="metric-bar" style={{ "--value": `${coveragePercentFromStatus(status)}%` } as CSSProperties} />
                    <p className="muted">{asList(item.requirements).slice(0, 3).join(", ") || item.recommendation || "No details returned."}</p>
                  </div>
                );
              })}
            </div>
            {!requirementCategories.length ? <p className="muted">Requirement categories were not returned for this run.</p> : null}
          </div>
        </div>

        <div className="section card">
          <h3>Skills evidence</h3>
          <table className="table">
            <thead>
              <tr>
                <th>Skill</th>
                <th>JD signal</th>
                <th>Resume evidence</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {skillsEvidenceRows.slice(0, 10).map((item, index) => (
                <tr key={`${item.skill ?? "skill"}-${index}`}>
                  <td>{item.skill}</td>
                  <td className="muted">{item.jdSignal}</td>
                  <td className="muted">{item.resumeEvidence}</td>
                  <td>
                    <span className={`status ${statusClass(item.status)}`}>
                      {item.status}
                    </span>
                  </td>
                </tr>
              ))}
              {!skillsEvidenceRows.length ? (
                <tr>
                  <td colSpan={4} className="muted">No skills evidence reported.</td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>

        <div className="section grid two">
          <div className="card">
            <h3>Missing skills</h3>
            <table className="table">
              <thead>
                <tr>
                  <th>Skill</th>
                  <th>Importance</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {asList(skills.missing_skills).slice(0, 8).map((item, index) => (
                  <tr key={`${item.skill ?? "skill"}-${index}`}>
                    <td>{item.skill ?? item.requirement ?? "Missing requirement"}</td>
                    <td>{item.importance ?? item.priority ?? "Important"}</td>
                    <td>{item.action ?? item.recommendation ?? "Add evidence if true."}</td>
                  </tr>
                ))}
                {!asList(skills.missing_skills).length ? (
                  <tr>
                    <td colSpan={3} className="muted">No missing skills reported.</td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
          <div className="card">
            <h3>Unsupported claims</h3>
            {unsupportedClaims.slice(0, 6).map((item, index) => (
              <p key={index}>
                <strong>{item.claim_or_skill ?? item.finding ?? "Claim to verify"}</strong>
                <br />
                <span className="muted">{item.evidence ?? item.resume_evidence ?? "Not found in resume."}</span>
              </p>
            ))}
            {!unsupportedClaims.length ? <p className="muted">No unsupported claims reported.</p> : null}
          </div>
        </div>

        <div className="section card">
          <h3>ATS formatting checks</h3>
          <p className="muted">
            Non-LLM checks for common parsing and screening issues. These are heuristics, so review the original file before applying.
          </p>
          <table className="table">
            <thead>
              <tr>
                <th>Check</th>
                <th>Status</th>
                <th>What it found</th>
                <th>Recommended action</th>
              </tr>
            </thead>
            <tbody>
              {atsFormattingChecks.map((item, index) => (
                <tr key={`${item.check ?? "check"}-${index}`}>
                  <td>
                    <strong>{item.check ?? "Formatting check"}</strong>
                    <br />
                    <span className="muted">{item.severity ?? "Low"} severity</span>
                  </td>
                  <td>
                    <span className={`status ${statusClass(item.status)}`}>{item.status ?? "Review"}</span>
                  </td>
                  <td className="muted">{item.detail ?? "No detail returned."}</td>
                  <td>{item.recommendation ?? "Review this item manually."}</td>
                </tr>
              ))}
              {!atsFormattingChecks.length ? (
                <tr>
                  <td colSpan={4} className="muted">
                    No formatting checks were saved for this run. Parse the resume through the Review screen to include them.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>

        <div className="section grid two">
          <div className="card">
            <h3>What else to fix before applying</h3>
            {additionalFixes.map((item, index) => (
              <p key={index}>
                <strong>{item.fix ?? item.recommendation ?? "Recommended fix"}</strong>
                <br />
                <span className="muted">
                  Impact: {item.impact ?? "Important"} · Effort: {item.effort ?? "Medium"}
                </span>
              </p>
            ))}
            {!additionalFixes.length ? <p className="muted">The highest-impact fixes are summarized in Apply Readiness.</p> : null}
          </div>
          <div className="card">
            <h3>Evidence findings</h3>
            {asList(analysis.confidence_findings).slice(0, 5).map((item, index) => (
              <p key={index}>
                <span className={`status ${String(item.confidence).toLowerCase() === "high" ? "good" : "warn"}`}>
                  {item.confidence ?? "needs review"}
                </span>{" "}
                <strong>{item.finding ?? "Finding"}</strong>
                <br />
                <span className="muted">{item.resume_evidence ?? item.evidence ?? "Not found in resume."}</span>
              </p>
            ))}
            {!asList(analysis.confidence_findings).length ? <p className="muted">Confidence findings will appear after a completed analysis.</p> : null}
          </div>
        </div>

        <div className="section">
          <div className="card action-card">
            <div>
              <span className="section-label">Job tracker</span>
              <h3>Save this opportunity</h3>
              <p className="muted">Stores the role, match score, top fixes, application status, and a link back to this analysis.</p>
            </div>
            <TrackerAction runId={run.run_id} initialStatus={tracker.status ?? "Not saved"} initialNotes={tracker.notes ?? ""} />
            <Link className="button secondary" href={`/tailor/${run.run_id}`}>
              Open Tailoring
            </Link>
          </div>
        </div>
      </section>
    );
  } catch (error) {
    return <ErrorPanel message={error instanceof Error ? error.message : "Unknown API error"} />;
  }
}

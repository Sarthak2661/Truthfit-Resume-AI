"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { API_URL } from "../../lib/api";
import type { ProviderInfo } from "../../lib/api";

type JobParseResult = {
  text: string;
  char_count: number;
  job_link: string;
  job_title: string;
  company: string;
  hard_requirements: string[];
  preferred_requirements: string[];
};

type ResumeParseResult = {
  filename: string;
  redacted_text: string;
  redacted_char_count: number;
  sections: Record<string, string>;
  ats_formatting_checks: AtsFormattingCheck[];
};

type AtsFormattingCheck = {
  check: string;
  status: string;
  severity: string;
  detail: string;
  recommendation: string;
};

export function JobAnalysisClient({ providers }: { providers: ProviderInfo[] }) {
  const resumeFormRef = useRef<HTMLFormElement>(null);
  const jobFormRef = useRef<HTMLFormElement>(null);
  const analysisFormRef = useRef<HTMLFormElement>(null);
  const [job, setJob] = useState<JobParseResult | null>(null);
  const [resume, setResume] = useState<ResumeParseResult | null>(null);
  const [resumeText, setResumeText] = useState("");
  const [resumeFileName, setResumeFileName] = useState("api-resume.txt");
  const [jobTextInput, setJobTextInput] = useState("");
  const [jobLinkInput, setJobLinkInput] = useState("");
  const [jobTitleInput, setJobTitleInput] = useState("");
  const [companyInput, setCompanyInput] = useState("");
  const [targetRegion, setTargetRegion] = useState("US");
  const [provider, setProvider] = useState(providers[0]?.name ?? "Gemini");
  const [model, setModel] = useState(providers[0]?.default_model ?? "");
  const [apiKey, setApiKey] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [parsingResume, setParsingResume] = useState(false);
  const [parsingJob, setParsingJob] = useState(false);

  const providerModels = providers.find((item) => item.name === provider)?.models ?? [];

  useEffect(() => {
    clearLegacyReviewStorage();
    setProvider(sessionStorage.getItem("truthfit.provider") ?? providers[0]?.name ?? "Gemini");
    setModel(sessionStorage.getItem("truthfit.model") ?? providers[0]?.default_model ?? "");
    setApiKey(sessionStorage.getItem("truthfit.apiKey") ?? "");
  }, []);

  useEffect(() => {
    const savedModel = sessionStorage.getItem("truthfit.model");
    if (savedModel && providerModels.includes(savedModel)) {
      setModel(savedModel);
      return;
    }

    setModel(providerModels[0] ?? "");
  }, [provider]);

  useEffect(() => {
    sessionStorage.setItem("truthfit.provider", provider);
  }, [provider]);

  useEffect(() => {
    sessionStorage.setItem("truthfit.model", model);
  }, [model]);

  useEffect(() => {
    sessionStorage.setItem("truthfit.apiKey", apiKey);
  }, [apiKey]);

  async function parseResume() {
    if (!resumeFormRef.current) {
      return;
    }

    const fileInput = resumeFormRef.current.elements.namedItem("file") as HTMLInputElement | null;
    if (!fileInput?.files?.length) {
      setError("Choose a resume file before parsing.");
      return;
    }

    setError("");
    setParsingResume(true);

    try {
      const form = new globalThis.FormData();
      form.set("file", fileInput.files[0]);
      const response = await fetch(`${API_URL}/resumes/parse`, { method: "POST", body: form });

      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        setError(body.detail ?? "Resume parsing failed.");
        return;
      }

      const parsed = (await response.json()) as ResumeParseResult;
      setResume(parsed);
      setResumeText(parsed.redacted_text);
      setResumeFileName(parsed.filename);
    } catch {
      setError("Resume parsing could not start in this browser. Refresh the page and try again.");
    } finally {
      setParsingResume(false);
    }
  }

  async function parseJob() {
    if (!jobFormRef.current) {
      return;
    }

    setError("");
    setParsingJob(true);

    try {
      const fileInput = jobFormRef.current.elements.namedItem("file") as HTMLInputElement | null;
      const pastedTextInput = jobFormRef.current.elements.namedItem("pasted_text") as HTMLTextAreaElement | null;
      const jobLinkField = jobFormRef.current.elements.namedItem("job_link") as HTMLInputElement | null;
      const pastedText = pastedTextInput?.value ?? jobTextInput;
      const jobLink = jobLinkField?.value ?? jobLinkInput;
      const hasFile = Boolean(fileInput?.files?.length);
      const body = hasFile ? new globalThis.FormData() : new URLSearchParams();

      if (hasFile && body instanceof globalThis.FormData && fileInput?.files?.[0]) {
        body.set("file", fileInput.files[0]);
      }

      body.set("pasted_text", pastedText);
      body.set("job_link", jobLink);

      const response = await fetch(`${API_URL}/jobs/parse`, { method: "POST", body });

      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        setError(body.detail ?? "Job parsing failed.");
        return;
      }

      const parsed = (await response.json()) as JobParseResult;
      setJob(parsed);
      setJobTextInput(parsed.text);
      setJobLinkInput(parsed.job_link);
      setJobTitleInput(parsed.job_title);
      setCompanyInput(parsed.company);
    } catch {
      setError("Requirements extraction could not start in this browser. Refresh the page and try again.");
    } finally {
      setParsingJob(false);
    }
  }

  async function runAnalysis() {
    if (!analysisFormRef.current) {
      return;
    }

    setLoading(true);
    setError("");

    const form = new FormData(analysisFormRef.current);
    const jobDescription = job?.text || String(form.get("job_description") ?? "");
    const jobLink = job?.job_link || String(form.get("job_link") ?? "");

    const response = await fetch(`${API_URL}/analysis/run`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        resume_text: resumeText,
        resume_file_name: resumeFileName,
        job_description: jobDescription,
        job_link: jobLink,
        job_title: form.get("job_title"),
        company: form.get("company"),
        include_cover_letter: form.get("include_cover_letter") === "on",
        user_projects: form.get("user_projects"),
        provider,
        model,
        api_key: apiKey,
        user_email: "",
        resume_formatting_checks: resume?.ats_formatting_checks ?? [],
        target_region: targetRegion,
      }),
    });

    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      setError(body.detail ?? "Analysis failed.");
      setLoading(false);
      return;
    }

    const created = await response.json();
    window.location.href = `/analysis/${created.run_id}`;
  }

  return (
    <div className="grid two">
      <form className="card form" ref={resumeFormRef} onSubmit={(event) => event.preventDefault()}>
        <span className="section-label">Resume</span>
        <h3>Upload and redact</h3>
        <label className="field">
          <span>Resume file</span>
          <input className="input" name="file" type="file" accept=".pdf,.docx,.txt" required />
        </label>
        <button className="button secondary" type="button" onClick={parseResume} disabled={parsingResume}>
          {parsingResume ? "Parsing resume..." : "Parse Resume"}
        </button>
        {resume || resumeText ? (
          <div className="success">
            Resume ready: {resume?.filename ?? resumeFileName}. Personal details are hidden before review.
          </div>
        ) : (
          <p className="muted">Start here. Upload a PDF, DOCX, or TXT resume and review the redacted evidence before running analysis.</p>
        )}
        {resume ? (
          <div>
            <span className="section-label">Detected sections</span>
            {Object.entries(resume.sections).slice(0, 4).map(([name, value]) => (
              <p className="muted" key={name}>
                <strong>{name}</strong>: {value.slice(0, 180)}
              </p>
            ))}
          </div>
        ) : null}
        {resume?.ats_formatting_checks?.length ? (
          <div>
            <span className="section-label">ATS formatting checks</span>
            <table className="table compact">
              <tbody>
                {resume.ats_formatting_checks.slice(0, 4).map((item) => (
                  <tr key={item.check}>
                    <td>
                      <strong>{item.check}</strong>
                      <br />
                      <span className="muted">{item.detail}</span>
                    </td>
                    <td>
                      <span className={`status ${statusClass(item.status)}`}>{item.status}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </form>

      <form className="card form" ref={jobFormRef} onSubmit={(event) => event.preventDefault()}>
        <span className="section-label">Job description</span>
        <h3>Extract requirements</h3>
        <label className="field">
          <span>Job file</span>
          <input className="input" name="file" type="file" accept=".pdf,.docx,.txt" />
        </label>
        <label className="field">
          <span>Paste JD</span>
          <textarea
            className="textarea"
            name="pasted_text"
            onChange={(event) => setJobTextInput(event.target.value)}
            placeholder="Paste the job description here..."
            value={jobTextInput}
          />
        </label>
        <label className="field">
          <span>Job link</span>
          <input
            className="input"
            name="job_link"
            onChange={(event) => setJobLinkInput(event.target.value)}
            placeholder="https://company.com/careers/job-id"
            value={jobLinkInput}
          />
        </label>
        <button className="button secondary" type="button" onClick={parseJob} disabled={parsingJob}>
          {parsingJob ? "Extracting requirements..." : "Extract Requirements"}
        </button>
        {job ? (
          <div className="success">
            JD ready: {job.char_count} characters. Found {job.hard_requirements.length} hard requirement(s) and{" "}
            {job.preferred_requirements.length} preferred signal(s).
          </div>
        ) : (
          <p className="muted">Paste the JD or upload a file, then extract the role signals before running the review.</p>
        )}
      </form>

      <form className="card form span-full" ref={analysisFormRef} onSubmit={(event) => event.preventDefault()}>
        <span className="section-label">Review setup</span>
        <h3>Run analysis</h3>
        {!resumeText ? <div className="alert">Upload and parse a resume above first.</div> : null}
        {!job ? <div className="alert">Extract the job description above before running the review.</div> : null}
        {job ? (
          <div className="grid two">
            <div>
              <span className="section-label">Hard requirements</span>
              {job.hard_requirements.slice(0, 5).map((item, index) => (
                <p className="muted" key={index}>{item}</p>
              ))}
            </div>
            <div>
              <span className="section-label">Preferred skills</span>
              {job.preferred_requirements.slice(0, 5).map((item, index) => (
                <p className="muted" key={index}>{item}</p>
              ))}
            </div>
          </div>
        ) : null}
        <div className="grid three">
          <label className="field">
            <span>Role title</span>
            <input
              className="input"
              name="job_title"
              onChange={(event) => setJobTitleInput(event.target.value)}
              placeholder="Data Engineer"
              value={jobTitleInput}
            />
          </label>
          <label className="field">
            <span>Company</span>
            <input
              className="input"
              name="company"
              onChange={(event) => setCompanyInput(event.target.value)}
              placeholder="Company name"
              value={companyInput}
            />
          </label>
          <label className="field">
            <span>Regional targeting</span>
            <select className="select" value={targetRegion} onChange={(event) => setTargetRegion(event.target.value)}>
              <option>US</option>
              <option>India</option>
              <option>GCC</option>
              <option>Canada/Europe</option>
            </select>
          </label>
        </div>
        <label className="field">
          <span>Provider</span>
          <select className="select" value={provider} onChange={(event) => setProvider(event.target.value)}>
            {providers.map((item) => (
              <option key={item.name}>{item.name}</option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>Model</span>
          <select className="select" value={model} onChange={(event) => setModel(event.target.value)}>
            {providerModels.map((item) => (
              <option key={item}>{item}</option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>Provider API key</span>
          <input className="input" value={apiKey} onChange={(event) => setApiKey(event.target.value)} type="password" />
        </label>
        <Link className="settings-link" href="/settings/providers">
          Advanced model settings
        </Link>
        <label className="field">
          <span>Project evidence</span>
          <textarea className="textarea" name="user_projects" placeholder="Paste project notes or public GitHub links..." />
        </label>
        <label>
          <input name="include_cover_letter" type="checkbox" /> Include cover letter
        </label>
        <input name="job_description" type="hidden" value={job?.text ?? ""} />
        <input name="job_link" type="hidden" value={job?.job_link ?? ""} />
        <button className="button" type="button" onClick={runAnalysis} disabled={loading || !resumeText || !job}>
          {loading ? "Running analysis..." : "Run Analysis"}
        </button>
        {error ? <div className="alert">{error}</div> : null}
      </form>
    </div>
  );
}

function clearLegacyReviewStorage() {
  [
    "truthfit.resumeParse",
    "truthfit.resumeText",
    "truthfit.resumeFileName",
    "truthfit.jobParse",
    "truthfit.jobText",
    "truthfit.jobLink",
    "truthfit.jobTitle",
    "truthfit.company",
  ].forEach((key) => localStorage.removeItem(key));
}

function statusClass(value: unknown): string {
  const normalized = String(value ?? "").toLowerCase();
  if (normalized.includes("pass") || normalized.includes("supported") || normalized.includes("good")) {
    return "good";
  }
  if (normalized.includes("fail") || normalized.includes("risk") || normalized.includes("missing")) {
    return "bad";
  }
  return "warn";
}

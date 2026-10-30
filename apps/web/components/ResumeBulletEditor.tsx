"use client";

import { useMemo, useState } from "react";

type BulletItem = {
  before?: string;
  original?: string;
  after?: string;
  rewritten?: string;
  evidence_used?: string;
  resume_evidence?: string;
  why_improved?: string;
  evidence_status?: string;
  verification_status?: string;
};

type EditorRow = {
  id: string;
  original: string;
  suggested: string;
  draft: string;
  evidence: string;
  evidenceStatus: string;
  decision: "pending" | "editing" | "accepted" | "rejected";
};

export function ResumeBulletEditor({ bullets }: { bullets: BulletItem[] }) {
  const initialRows = useMemo(
    () =>
      bullets.map((item, index) => ({
        id: `${index}-${item.before ?? item.original ?? "bullet"}`,
        original: item.before ?? item.original ?? "Original bullet not provided.",
        suggested: item.after ?? item.rewritten ?? "Suggested bullet not provided.",
        draft: item.after ?? item.rewritten ?? "Suggested bullet not provided.",
        evidence: item.evidence_used ?? item.resume_evidence ?? item.why_improved ?? "Existing resume or project evidence.",
        evidenceStatus: item.evidence_status ?? item.verification_status ?? "Needs review",
        decision: "pending" as const,
      })),
    [bullets],
  );
  const [rows, setRows] = useState<EditorRow[]>(initialRows);

  const acceptedCount = rows.filter((row) => row.decision === "accepted").length;
  const editedCount = rows.filter((row) => row.decision === "editing" && row.draft !== row.suggested).length;
  const rejectedCount = rows.filter((row) => row.decision === "rejected").length;
  const keptBullets = rows.filter((row) => row.decision !== "rejected").map((row) => row.draft.trim()).filter(Boolean);

  if (!rows.length) {
    return <p className="muted">No bullet rewrites returned for this run.</p>;
  }

  function updateRow(id: string, update: Partial<EditorRow>) {
    setRows((current) => current.map((row) => (row.id === id ? { ...row, ...update } : row)));
  }

  return (
    <div className="editor-list">
      <div className="editor-summary">
        <span className="pill">{acceptedCount} accepted</span>
        <span className="pill">{editedCount} edited</span>
        <span className="pill">{rejectedCount} rejected</span>
        <button className="button secondary compact-button" type="button" onClick={() => copyKeptBullets(keptBullets)}>
          Copy kept bullets
        </button>
      </div>

      {rows.map((row) => (
        <article className="editor-card" key={row.id}>
          <div className="editor-grid">
            <div>
              <span className="section-label">Original bullet</span>
              <p>{row.original}</p>
            </div>
            <label className="field">
              <span>Suggested bullet</span>
              <textarea
                className="textarea editor-textarea"
                value={row.draft}
                onChange={(event) => updateRow(row.id, { draft: event.target.value, decision: "editing" })}
              />
            </label>
          </div>

          <div className="editor-meta">
            <div>
              <span className="section-label">Evidence used</span>
              <p className="muted">{row.evidence}</p>
            </div>
            <span className={`status ${statusClass(row.evidenceStatus)}`}>{row.evidenceStatus}</span>
            <span className={`status ${decisionClass(row.decision)}`}>{decisionLabel(row.decision)}</span>
          </div>

          <div className="editor-actions">
            <button className="button secondary" type="button" onClick={() => updateRow(row.id, { decision: "editing" })}>
              Edit
            </button>
            <button className="button" type="button" onClick={() => updateRow(row.id, { decision: "accepted" })}>
              Accept
            </button>
            <button className="button danger" type="button" onClick={() => updateRow(row.id, { decision: "rejected", draft: row.suggested })}>
              Reject
            </button>
          </div>
        </article>
      ))}
    </div>
  );
}

async function copyKeptBullets(bullets: string[]) {
  if (!bullets.length || !navigator.clipboard) {
    return;
  }

  await navigator.clipboard.writeText(bullets.map((bullet) => `- ${bullet}`).join("\n"));
}

function statusClass(value: string): string {
  const normalized = value.toLowerCase();
  if (normalized.includes("support") || normalized.includes("verified") || normalized.includes("high")) {
    return "good";
  }
  if (normalized.includes("missing") || normalized.includes("unsupported") || normalized.includes("risk")) {
    return "bad";
  }
  return "warn";
}

function decisionClass(value: EditorRow["decision"]): string {
  if (value === "accepted") {
    return "good";
  }
  if (value === "rejected") {
    return "bad";
  }
  return "warn";
}

function decisionLabel(value: EditorRow["decision"]): string {
  if (value === "accepted") {
    return "Accepted";
  }
  if (value === "rejected") {
    return "Rejected";
  }
  if (value === "editing") {
    return "Editing";
  }
  return "Pending";
}

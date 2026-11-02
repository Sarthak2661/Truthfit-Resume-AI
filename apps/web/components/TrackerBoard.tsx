"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { authenticatedFetch } from "../lib/authenticated-fetch";
import type { TrackerItem } from "../lib/api-types";

const statuses = ["Saved", "Applied", "Interview", "Rejected"];

export function TrackerBoard({ initialJobs }: { initialJobs: TrackerItem[] }) {
  const [jobs, setJobs] = useState(initialJobs);
  const [query, setQuery] = useState("");
  const [priority, setPriority] = useState("All");
  const [sort, setSort] = useState("Follow-up");
  const [message, setMessage] = useState("");

  const visibleJobs = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    const filtered = jobs.filter((job) => {
      const matchesQuery = !normalizedQuery || `${job.role} ${job.company} ${job.location}`.toLowerCase().includes(normalizedQuery);
      return matchesQuery && (priority === "All" || job.priority === priority);
    });
    return filtered.sort((left, right) => {
      if (sort === "Match") return right.match_score - left.match_score;
      if (sort === "Priority") return priorityRank(left.priority) - priorityRank(right.priority);
      return dateRank(left.follow_up_date) - dateRank(right.follow_up_date);
    });
  }, [jobs, priority, query, sort]);

  async function updateJob(job: TrackerItem, changes: Partial<TrackerItem>) {
    const optimistic = { ...job, ...changes };
    setJobs((current) => current.map((item) => item.run_id === job.run_id ? optimistic : item));
    setMessage("");
    try {
      const response = await authenticatedFetch(`/tracker/${job.run_id}`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ status: optimistic.tracker_status, notes: optimistic.notes, priority: optimistic.priority, applied_at: optimistic.applied_at, follow_up_date: optimistic.follow_up_date }),
      });
      if (!response.ok) throw new Error("Tracker update failed.");
      const saved = await response.json() as TrackerItem;
      setJobs((current) => current.map((item) => item.run_id === saved.run_id ? saved : item));
    } catch {
      setJobs((current) => current.map((item) => item.run_id === job.run_id ? job : item));
      setMessage("A tracker change could not be saved. Your previous value was restored.");
    }
  }

  return (
    <>
      <div className="tracker-toolbar">
        <label className="field tracker-search"><span>Search</span><input className="input" onChange={(event) => setQuery(event.target.value)} placeholder="Role, company, or location" value={query} /></label>
        <label className="field"><span>Priority</span><select className="select" onChange={(event) => setPriority(event.target.value)} value={priority}><option>All</option><option>High</option><option>Normal</option><option>Low</option></select></label>
        <label className="field"><span>Sort by</span><select className="select" onChange={(event) => setSort(event.target.value)} value={sort}><option>Follow-up</option><option>Priority</option><option>Match</option></select></label>
        <div className="tracker-total"><span className="section-label">Visible roles</span><strong>{visibleJobs.length}</strong></div>
      </div>
      {message ? <div className="alert">{message}</div> : null}

      <div className="section kanban">
        {statuses.map((column) => {
          const columnJobs = visibleJobs.filter((job) => job.tracker_status === column);
          return (
            <section className="kanban-column" key={column}>
              <div className="kanban-head"><h3>{column}</h3><span className={`status ${statusClass(column)}`}>{columnJobs.length}</span></div>
              <div className="kanban-stack">
                {columnJobs.map((job) => (
                  <article className="job-card compact-job-card" key={job.run_id}>
                    <div className="job-card-title">
                      <div><span className="section-label">{job.company}</span><h3>{job.role}</h3><p className="muted">{job.location || "Location not specified"}</p></div>
                      <span className={`priority-dot priority-${job.priority.toLowerCase()}`} title={`${job.priority} priority`} />
                    </div>
                    <div className="job-card-meta"><span className="pill">{job.match_score}/100 match</span>{job.follow_up_date ? <span className="status warn">Follow up {formatDate(job.follow_up_date)}</span> : null}</div>
                    <label className="field compact-field"><span>Status</span><select className="select" value={job.tracker_status} onChange={(event) => updateJob(job, { tracker_status: event.target.value })}>{statuses.map((item) => <option key={item}>{item}</option>)}</select></label>
                    <details className="job-card-details">
                      <summary>Job details and notes</summary>
                      <div className="job-card-form">
                        <label className="field"><span>Priority</span><select className="select" value={job.priority} onChange={(event) => updateJob(job, { priority: event.target.value })}><option>High</option><option>Normal</option><option>Low</option></select></label>
                        <label className="field"><span>Applied date</span><input className="input" type="date" value={job.applied_at} onChange={(event) => updateJob(job, { applied_at: event.target.value })} /></label>
                        <label className="field"><span>Follow-up date</span><input className="input" type="date" value={job.follow_up_date} onChange={(event) => updateJob(job, { follow_up_date: event.target.value })} /></label>
                        <label className="field"><span>Notes</span><textarea className="textarea notes-input" value={job.notes} onChange={(event) => setJobs((current) => current.map((item) => item.run_id === job.run_id ? { ...item, notes: event.target.value } : item))} onBlur={(event) => updateJob(job, { notes: event.target.value })} /></label>
                        {job.top_fixes[0] ? <div><span className="section-label">Next resume fix</span><p className="muted">{job.top_fixes[0]}</p></div> : null}
                      </div>
                    </details>
                    <div className="job-card-actions"><Link className="button secondary" href={job.analysis_url}>Open analysis</Link>{job.job_link ? <a className="text-link" href={job.job_link} target="_blank" rel="noreferrer">Job post</a> : null}</div>
                  </article>
                ))}
                {!columnJobs.length ? <div className="kanban-empty"><span>No {column.toLowerCase()} roles</span></div> : null}
              </div>
            </section>
          );
        })}
      </div>
    </>
  );
}

function statusClass(value: string): string {
  if (value === "Interview") return "good";
  if (value === "Rejected") return "bad";
  return "warn";
}

function formatDate(value: string): string {
  const date = new Date(`${value}T00:00:00`);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString("en", { month: "short", day: "numeric" });
}

function priorityRank(value: string): number {
  return ({ High: 0, Normal: 1, Low: 2 } as Record<string, number>)[value] ?? 3;
}

function dateRank(value: string): number {
  if (!value) return Number.MAX_SAFE_INTEGER;
  const timestamp = new Date(`${value}T00:00:00`).getTime();
  return Number.isNaN(timestamp) ? Number.MAX_SAFE_INTEGER : timestamp;
}

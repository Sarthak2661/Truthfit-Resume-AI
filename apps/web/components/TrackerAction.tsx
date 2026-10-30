"use client";

import { useState } from "react";
import { API_URL } from "../lib/api";

const statuses = ["Saved", "Applied", "Interview", "Rejected"];

export function TrackerAction({
  runId,
  initialStatus = "Not saved",
  initialNotes = "",
}: {
  runId: string;
  initialStatus?: string;
  initialNotes?: string;
}) {
  const [status, setStatus] = useState(initialStatus === "Not saved" ? "Saved" : initialStatus);
  const [notes, setNotes] = useState(initialNotes);
  const [message, setMessage] = useState("");
  const [saving, setSaving] = useState(false);

  async function saveJob(nextStatus = status) {
    setSaving(true);
    setMessage("");

    try {
      const response = await fetch(`${API_URL}/tracker/${runId}`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ status: nextStatus, notes }),
      });

      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        setMessage(body.detail ?? "Tracker update failed.");
        return;
      }

      const saved = await response.json();
      setStatus(saved.tracker_status);
      setMessage("Saved to tracker.");
    } catch {
      setMessage("Could not reach the tracker API.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="tracker-action">
      <label className="field">
        <span>Job status</span>
        <select
          className="select"
          value={status}
          onChange={(event) => {
            setStatus(event.target.value);
            saveJob(event.target.value);
          }}
        >
          {statuses.map((item) => (
            <option key={item}>{item}</option>
          ))}
        </select>
      </label>
      <button className="button" type="button" onClick={() => saveJob()} disabled={saving}>
        {saving ? "Saving..." : "Save current job"}
      </button>
      <label className="field">
        <span>Notes</span>
        <textarea
          className="textarea notes-input"
          onChange={(event) => setNotes(event.target.value)}
          placeholder="Follow-up date, referral, recruiter name, or application notes..."
          value={notes}
        />
      </label>
      {message ? <p className="muted">{message}</p> : null}
    </div>
  );
}

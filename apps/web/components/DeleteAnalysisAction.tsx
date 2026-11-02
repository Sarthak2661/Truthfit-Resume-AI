"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { authenticatedFetch } from "../lib/authenticated-fetch";

export function DeleteAnalysisAction({ runId }: { runId: string }) {
  const router = useRouter();
  const [deleting, setDeleting] = useState(false);

  async function deleteAnalysis() {
    if (!window.confirm("Delete this analysis and its stored evidence? This cannot be undone.")) return;
    setDeleting(true);
    const response = await authenticatedFetch(`/analysis/${runId}`, { method: "DELETE" });
    if (!response.ok) {
      setDeleting(false);
      window.alert("The analysis could not be deleted. Please retry.");
      return;
    }
    router.push("/dashboard");
    router.refresh();
  }

  return (
    <button className="button danger secondary" disabled={deleting} onClick={deleteAnalysis} type="button">
      {deleting ? "Deleting..." : "Delete analysis"}
    </button>
  );
}

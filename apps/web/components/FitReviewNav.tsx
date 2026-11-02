"use client";

import type { MouseEvent } from "react";

const sections = [
  ["overview", "Overview"],
  ["requirements", "Requirements"],
  ["evidence", "Evidence"],
  ["ats-checks", "ATS checks"],
  ["actions", "Actions"],
];

export function FitReviewNav() {
  function openSection(event: MouseEvent<HTMLAnchorElement>, id: string) {
    const target = document.getElementById(id);
    if (!target) return;

    event.preventDefault();
    if (target instanceof HTMLDetailsElement) target.open = true;
    window.history.replaceState(null, "", `#${id}`);
    window.requestAnimationFrame(() => target.scrollIntoView({ behavior: "smooth", block: "start" }));
  }

  return (
    <nav className="analysis-nav" aria-label="Fit review sections">
      {sections.map(([id, label]) => (
        <a href={`#${id}`} key={id} onClick={(event) => openSection(event, id)}>{label}</a>
      ))}
    </nav>
  );
}

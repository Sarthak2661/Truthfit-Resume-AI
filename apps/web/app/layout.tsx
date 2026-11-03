import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";
import { AuthControls } from "../components/AuthControls";
import { ThemeToggle } from "../components/ThemeToggle";

export const metadata: Metadata = {
  title: "TruthFit Resume AI",
  description: "Product-style resume and job-fit review workspace.",
};

const links = [
  ["/", "Home"],
  ["/dashboard", "Dashboard"],
  ["/jobs", "Analyze"],
  ["/tracker", "Tracker"],
];

const themeScript = `
  (() => {
    try {
      sessionStorage.removeItem("truthfit.apiKey");
      localStorage.removeItem("truthfit.apiKey");
      const saved = localStorage.getItem("truthfit-theme");
      const preferred = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
      document.documentElement.dataset.theme = saved === "dark" || saved === "light" ? saved : preferred;
    } catch (_) {
      document.documentElement.dataset.theme = "light";
    }
  })();
`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body suppressHydrationWarning>
        <div className="shell">
          <header className="topbar">
            <Link className="brand" href="/">
              <span className="brand-mark">TF</span>
              <span>TruthFit Resume AI</span>
            </Link>
            <nav className="nav" aria-label="Primary navigation">
              {links.map(([href, label]) => (
                <Link key={href} href={href}>
                  {label}
                </Link>
              ))}
              <ThemeToggle />
              <AuthControls />
            </nav>
          </header>
          <main className="main">{children}</main>
          <footer className="site-footer">
            <span>TruthFit Resume AI</span>
            <nav aria-label="Support and legal links">
              <Link href="/privacy">Privacy</Link>
              <Link href="/terms">Terms</Link>
              <a href="https://github.com/Sarthak2661/Truthfit-Resume-AI" rel="noreferrer" target="_blank">GitHub</a>
              <a href="https://github.com/Sarthak2661/Truthfit-Resume-AI/issues" rel="noreferrer" target="_blank">Report an issue</a>
              <a href="mailto:sarthak2661@gmail.com">Contact</a>
            </nav>
          </footer>
        </div>
      </body>
    </html>
  );
}

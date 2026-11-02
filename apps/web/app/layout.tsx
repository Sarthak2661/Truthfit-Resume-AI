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
        </div>
      </body>
    </html>
  );
}

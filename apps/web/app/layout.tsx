import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

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

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
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
            </nav>
          </header>
          <main className="main">{children}</main>
        </div>
      </body>
    </html>
  );
}

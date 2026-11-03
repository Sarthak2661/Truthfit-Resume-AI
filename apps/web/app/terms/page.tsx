import Link from "next/link";

export default function TermsPage() {
  return (
    <article className="legal-page">
      <span className="section-label">Terms of use</span>
      <h1>Terms for using TruthFit</h1>
      <p className="legal-updated">Last updated: November 3, 2026</p>

      <section><h2>Purpose</h2><p>TruthFit is a resume-review and job-search aid. It does not make hiring decisions, guarantee interviews, reproduce an employer&apos;s ATS, or provide legal, immigration, or employment advice.</p></section>
      <section><h2>Your responsibilities</h2><p>You must provide accurate information, upload only documents you are allowed to process, verify every suggested claim before using it, and keep your account and provider credentials secure.</p></section>
      <section><h2>AI-assisted output</h2><p>Analysis may be incomplete, inconsistent, or wrong. Scores are advisory, and TruthFit is not an ATS or hiring-decision system. You must verify all generated content before using it. Never add an unsupported claim, skill, result, or responsibility to a resume.</p></section>
      <section><h2>Acceptable use</h2><p>Do not use TruthFit to upload another person&apos;s private data without permission, evade security controls, overload the service, generate deceptive qualifications, or violate provider or platform rules.</p></section>
      <section><h2>Availability</h2><p>The public beta may enforce quotas, change features, experience outages, or remove stored data under the documented retention policy. The service is provided without a guarantee of uninterrupted availability.</p></section>
      <section><h2>Accounts and termination</h2><p>You may stop using the service and delete application data at any time. Access may be limited for abuse, security risk, or repeated violation of these terms.</p></section>
      <section><h2>Liability</h2><p>Use the service at your own judgment. To the extent permitted by law, the project maintainers are not liable for hiring outcomes, lost opportunities, provider actions, or indirect loss arising from use of the service.</p></section>
      <p className="legal-contact">By creating an account, you agree to these terms and the <Link href="/privacy">Privacy Notice</Link>.</p>
    </article>
  );
}

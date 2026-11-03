import Link from "next/link";

export default function PrivacyPage() {
  return (
    <article className="legal-page">
      <span className="section-label">Privacy notice</span>
      <h1>How TruthFit handles your data</h1>
      <p className="legal-updated">Last updated: November 3, 2026</p>

      <section><h2>What we process</h2><p>TruthFit processes account details, resumes, job descriptions, analysis results, and tracker notes needed to provide the service. Resume and job text may contain personal or sensitive information, so only upload content you are authorized to use.</p></section>
      <section><h2>What is redacted</h2><p>Before live analysis, TruthFit attempts to remove common names, email addresses, phone numbers, profile URLs, and street-style addresses. Redaction is best-effort and may not detect every personal detail or unusual resume layout.</p></section>
      <section><h2>Analysis providers</h2><p>When you start an analysis, redacted resume text and the job description are sent to the provider you select: Gemini, Claude, OpenAI, or Perplexity. The selected provider is shown beside the Analyze button. Provider handling is also governed by that provider&apos;s terms and privacy policy.</p></section>
      <section><h2>Storage and retention</h2><p>TruthFit stores redacted resume text, job details, results, and operational events for your account. Original resume text is discarded unless you explicitly enable encrypted retention. The default retention periods are 30 days for completed runs, 7 days for failed runs, and 1 day for pending runs; a deployment may configure different periods.</p></section>
      <section><h2>API keys</h2><p>Bring-your-own provider keys remain in page memory and are not written to browser storage or application logs. Public queued deployments use server-managed provider credentials instead.</p></section>
      <section><h2>Your choices</h2><p>You can inspect stored-data counts and delete an individual analysis or all TruthFit application data in Settings. Deleting application data does not delete the Supabase authentication identity. For account-identity deletion or support, use the repository support link below.</p></section>
      <section><h2>Security and limitations</h2><p>TruthFit uses account isolation, encrypted transport on deployed services, request limits, and structured validation. No system is risk-free, and TruthFit is not a compliance-grade anonymization service.</p></section>
      <p className="legal-contact">Questions or deletion help: <a href="https://github.com/Sarthak2661/Truthfit-Resume-AI/issues">open a support issue</a>. Also review the <Link href="/terms">Terms of Use</Link>.</p>
    </article>
  );
}

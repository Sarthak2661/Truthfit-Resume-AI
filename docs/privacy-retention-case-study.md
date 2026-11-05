# Case Study: Privacy and Retention by Default

## The Problem

Resumes contain names, contact details, employment history, education, and location data. A useful review product must process enough of that content to compare evidence with a job description, but retaining every original document would create unnecessary exposure.

## Design Decision

TruthFit separates transient processing data from persisted product data.

- Resume text is redacted before provider analysis and persistence.
- Original resume text is transient by default.
- Original text is retained only after explicit opt-in and is encrypted with AES-GCM.
- Job descriptions and structured results are retained only until their configured expiry or user deletion.
- Provider credentials remain in browser memory for local BYOK use and are removed from production queue payloads.
- Analysis consent, prompt version, and schema version are recorded with each run.
- Account ownership is derived from a verified Supabase JWT, never from a client-provided email.

## Failure Modes Considered

Heuristic redaction can miss unusual resume layouts, so the UI and documentation describe it as best-effort rather than compliance-grade anonymization. Encryption protects retained content at rest but does not remove the need for key rotation and access control. Deleting TruthFit application data does not currently delete the Supabase login identity; that remains a separate lifecycle task.

Provider failures and malformed responses do not become successful zero-score analyses. The pending run transitions to failed, the error category is retained without sensitive document text, and cleanup applies a shorter failed-run retention period.

## Verification

Automated tests cover common resume-header redaction patterns, authenticated encryption, default redacted-only persistence, explicit retention, cross-account access, deletion, expiry cleanup, prompt injection, and log-field allowlisting. A separate PostgreSQL drill uses `pg_dump` and `pg_restore` to compare core-table counts in an isolated temporary database:

```powershell
python scripts/verify_backup_restore.py
```

The drill can use a separate `TRUTHFIT_ADMIN_DATABASE_URL` for the isolated restore database, so
the application role does not need ongoing database-creation privileges.

## Trade-Off

The design intentionally favors data minimization over recreating the original uploaded file. That reduces exposure but means the product cannot yet offer a fully editable, pixel-preserving resume document. A future document editor should store user-approved structured sections rather than silently retaining the original file.

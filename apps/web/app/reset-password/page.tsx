"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import type { Session } from "@supabase/supabase-js";

import { createClient } from "../../lib/supabase/client";

export default function ResetPasswordPage() {
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionReady, setSessionReady] = useState<boolean | null>(null);

  useEffect(() => {
    createClient().auth.getSession().then((result: { data: { session: Session | null } }) => {
      setSessionReady(Boolean(result.data.session));
    });
  }, []);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (password.length < 8) {
      setMessage("Use a password with at least 8 characters.");
      return;
    }
    if (password !== confirmPassword) {
      setMessage("The passwords do not match.");
      return;
    }

    setLoading(true);
    setMessage("");
    try {
      const { error } = await createClient().auth.updateUser({ password });
      if (error) {
        setMessage(error.message);
        return;
      }
      window.location.assign("/dashboard");
    } catch {
      setMessage("The password could not be updated. Request a new reset link and try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="auth-page">
      <form className="card auth-card" onSubmit={submit}>
        <div className="auth-heading">
          <div className="section-label">Account recovery</div>
          <h1>Choose a new password</h1>
          <p className="muted">Use at least 8 characters and avoid reusing a password from another service.</p>
        </div>
        {sessionReady === false ? (
          <div className="alert" role="alert">
            This reset link is invalid or expired. <Link href="/login?error=expired_link">Request a new link</Link>.
          </div>
        ) : null}
        <label className="field">
          <span>New password</span>
          <input autoComplete="new-password" className="input" minLength={8} onChange={(event) => setPassword(event.target.value)} required type="password" value={password} />
        </label>
        <label className="field">
          <span>Confirm new password</span>
          <input autoComplete="new-password" className="input" minLength={8} onChange={(event) => setConfirmPassword(event.target.value)} required type="password" value={confirmPassword} />
        </label>
        <button className="button" disabled={loading || sessionReady !== true} type="submit">{loading ? "Updating password..." : sessionReady === null ? "Checking reset link..." : "Update password"}</button>
        {message ? <div className="alert" role="status">{message}</div> : null}
      </form>
    </section>
  );
}

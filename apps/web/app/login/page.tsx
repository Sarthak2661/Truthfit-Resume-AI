"use client";

import HCaptcha from "@hcaptcha/react-hcaptcha";
import { FormEvent, useRef, useState } from "react";

import { createClient } from "../../lib/supabase/client";

type AuthMode = "sign-in" | "create-account";

export default function LoginPage() {
  const [mode, setMode] = useState<AuthMode>("sign-in");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [captchaToken, setCaptchaToken] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const captchaRef = useRef<HCaptcha>(null);
  const captchaSiteKey = process.env.NEXT_PUBLIC_HCAPTCHA_SITE_KEY?.trim() ?? "";

  function resetCaptcha() {
    captchaRef.current?.resetCaptcha();
    setCaptchaToken("");
  }

  function changeMode(nextMode: AuthMode) {
    setMode(nextMode);
    setMessage("");
    resetCaptcha();
  }

  async function signIn() {
    const normalizedEmail = email.trim();
    if (!normalizedEmail) {
      setMessage("Enter your email address.");
      return;
    }
    if (captchaSiteKey && !captchaToken) {
      setMessage("Complete the CAPTCHA verification before signing in.");
      return;
    }

    setLoading(true);
    setMessage("");
    try {
      const { error } = await createClient().auth.signInWithPassword({
        email: normalizedEmail,
        password,
        options: captchaToken ? { captchaToken } : undefined,
      });
      if (error) {
        setMessage(error.message);
        return;
      }
      window.location.assign("/dashboard");
    } catch {
      setMessage("Sign-in could not reach the authentication service. Try again.");
    } finally {
      setLoading(false);
      resetCaptcha();
    }
  }

  async function createAccount() {
    const normalizedName = fullName.trim();
    const normalizedEmail = email.trim();
    if (normalizedName.length < 2) {
      setMessage("Enter your full name.");
      return;
    }
    if (!normalizedEmail) {
      setMessage("Enter your email address.");
      return;
    }
    if (password.length < 8) {
      setMessage("Use a password with at least 8 characters.");
      return;
    }
    if (password !== confirmPassword) {
      setMessage("The passwords do not match.");
      return;
    }
    if (!acceptedTerms) {
      setMessage("Accept the terms and privacy notice to continue.");
      return;
    }
    if (!captchaSiteKey) {
      setMessage("CAPTCHA is not configured yet. Add the hCaptcha site key to the web environment.");
      return;
    }
    if (!captchaToken) {
      setMessage("Complete the CAPTCHA verification before creating your account.");
      return;
    }

    setLoading(true);
    setMessage("");
    try {
      const { data, error } = await createClient().auth.signUp({
        email: normalizedEmail,
        password,
        options: {
          captchaToken,
          data: { full_name: normalizedName },
          emailRedirectTo: `${window.location.origin}/auth/callback`,
        },
      });
      if (error) {
        setMessage(error.message);
        return;
      }
      if (data.session) {
        window.location.assign("/dashboard");
        return;
      }
      setMessage("Check your email to confirm your account, then sign in.");
    } catch {
      setMessage("Account creation could not reach the authentication service. Try again.");
    } finally {
      setLoading(false);
      resetCaptcha();
    }
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (mode === "create-account") {
      await createAccount();
      return;
    }
    await signIn();
  }

  const creatingAccount = mode === "create-account";

  return (
    <section className="auth-page">
      <form className={`card auth-card ${creatingAccount ? "auth-card-wide" : ""}`} onSubmit={submit}>
        <div className="auth-heading">
          <div className="section-label">Secure workspace</div>
          <h1>{creatingAccount ? "Create your TruthFit account" : "Sign in to TruthFit"}</h1>
          <p className="muted">
            {creatingAccount
              ? "Keep your resume reviews and tracked applications private to your account."
              : "Your analyses and tracked jobs are visible only to your account."}
          </p>
        </div>

        {creatingAccount ? (
          <label className="field">
            <span>Full name</span>
            <input autoComplete="name" className="input" onChange={(event) => setFullName(event.target.value)} required type="text" value={fullName} />
          </label>
        ) : null}

        <label className="field">
          <span>Email</span>
          <input autoComplete="email" className="input" onChange={(event) => setEmail(event.target.value)} required type="email" value={email} />
        </label>

        <div className={creatingAccount ? "auth-password-grid" : ""}>
          <label className="field">
            <span>Password</span>
            <input
              autoComplete={creatingAccount ? "new-password" : "current-password"}
              className="input"
              minLength={8}
              onChange={(event) => setPassword(event.target.value)}
              required
              type="password"
              value={password}
            />
          </label>
          {creatingAccount ? (
            <label className="field">
              <span>Confirm password</span>
              <input autoComplete="new-password" className="input" minLength={8} onChange={(event) => setConfirmPassword(event.target.value)} required type="password" value={confirmPassword} />
            </label>
          ) : null}
        </div>

        {creatingAccount ? (
          <label className="auth-consent">
            <input checked={acceptedTerms} onChange={(event) => setAcceptedTerms(event.target.checked)} required type="checkbox" />
            <span>I agree to the Terms of Use and Privacy Notice.</span>
          </label>
        ) : null}

        {captchaSiteKey ? (
          <div className="captcha-wrap">
            <HCaptcha onExpire={() => setCaptchaToken("")} onVerify={(token) => setCaptchaToken(token)} ref={captchaRef} sitekey={captchaSiteKey} />
          </div>
        ) : creatingAccount ? (
          <div className="auth-config-note">CAPTCHA setup is required before account creation can be enabled.</div>
        ) : null}

        <button className="button" disabled={loading} type="submit">
          {loading ? (creatingAccount ? "Creating account..." : "Signing in...") : creatingAccount ? "Create account" : "Sign in"}
        </button>

        <div className="auth-switch">
          <span>{creatingAccount ? "Already have an account?" : "New to TruthFit?"}</span>
          <button className="auth-switch-button" disabled={loading} onClick={() => changeMode(creatingAccount ? "sign-in" : "create-account")} type="button">
            {creatingAccount ? "Sign in" : "Create account"}
          </button>
        </div>

        {message ? <div className="alert" role="status">{message}</div> : null}
      </form>
    </section>
  );
}

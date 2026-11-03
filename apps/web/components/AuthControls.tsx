"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import type { AuthChangeEvent, Session, User } from "@supabase/supabase-js";

import { createClient } from "../lib/supabase/client";
import { e2eAuthBypassEnabled } from "../lib/e2e-auth";

export function AuthControls() {
  const e2eBypass = e2eAuthBypassEnabled();
  const [email, setEmail] = useState(e2eBypass ? "e2e@truthfit.local" : "");

  useEffect(() => {
    if (e2eBypass) {
      return;
    }
    const supabase = createClient();
    supabase.auth.getUser().then((result: { data: { user: User | null } }) => {
      setEmail(result.data.user?.email ?? "");
    });
    const { data } = supabase.auth.onAuthStateChange((
      _event: AuthChangeEvent,
      session: Session | null,
    ) => {
      setEmail(session?.user.email ?? "");
    });
    return () => data.subscription.unsubscribe();
  }, [e2eBypass]);

  async function signOut() {
    if (e2eBypass) {
      window.location.assign("/");
      return;
    }
    await createClient().auth.signOut();
    window.location.assign("/");
  }

  if (!email) {
    return (
      <Link className="button auth-button" href="/login">
        Sign in
      </Link>
    );
  }

  return (
    <div className="auth-controls">
      <span className="auth-email" title={email}>{email}</span>
      <button className="button secondary auth-button" type="button" onClick={signOut}>
        Sign out
      </button>
    </div>
  );
}

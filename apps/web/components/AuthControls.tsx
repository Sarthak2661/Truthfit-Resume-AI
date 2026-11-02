"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import type { AuthChangeEvent, Session, User } from "@supabase/supabase-js";

import { createClient } from "../lib/supabase/client";

export function AuthControls() {
  const [email, setEmail] = useState("");

  useEffect(() => {
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
  }, []);

  async function signOut() {
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

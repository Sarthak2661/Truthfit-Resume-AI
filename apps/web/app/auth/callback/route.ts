import { NextResponse } from "next/server";

import { createClient } from "../../../lib/supabase/server";

export async function GET(request: Request) {
  const requestUrl = new URL(request.url);
  const code = requestUrl.searchParams.get("code");
  const authError = requestUrl.searchParams.get("error_code");
  if (authError) {
    const reason = authError === "otp_expired" ? "expired_link" : "confirmation_failed";
    return NextResponse.redirect(new URL(`/login?error=${reason}`, requestUrl.origin));
  }
  const requestedNext = requestUrl.searchParams.get("next");
  const nextPath = requestedNext === "/reset-password" ? requestedNext : "/dashboard?confirmed=1";
  if (code) {
    const supabase = await createClient();
    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (!error) {
      return NextResponse.redirect(new URL(nextPath, requestUrl.origin));
    }
  }
  return NextResponse.redirect(new URL("/login?error=confirmation_failed", requestUrl.origin));
}

export function e2eAuthBypassEnabled(): boolean {
  return (
    process.env.NODE_ENV !== "production" &&
    process.env.NEXT_PUBLIC_TRUTHFIT_E2E_AUTH_BYPASS === "1"
  );
}

export const E2E_AUTH_TOKEN = "truthfit-e2e-token";

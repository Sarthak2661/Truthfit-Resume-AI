const DEVELOPMENT_API_URL = "http://127.0.0.1:8000";

export const API_URL = resolveApiUrl();

function resolveApiUrl(): string {
  const configuredUrl = process.env.NEXT_PUBLIC_TRUTHFIT_API_URL?.trim();
  if (!configuredUrl) {
    if (process.env.NODE_ENV === "production") {
      throw new Error("NEXT_PUBLIC_TRUTHFIT_API_URL is required for production builds.");
    }
    return DEVELOPMENT_API_URL;
  }

  let parsed: URL;
  try {
    parsed = new URL(configuredUrl);
  } catch {
    throw new Error("NEXT_PUBLIC_TRUTHFIT_API_URL must be a valid absolute URL.");
  }

  if (!["http:", "https:"].includes(parsed.protocol)) {
    throw new Error("NEXT_PUBLIC_TRUTHFIT_API_URL must use HTTP or HTTPS.");
  }
  return configuredUrl.replace(/\/+$/, "");
}

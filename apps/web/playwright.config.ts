import { defineConfig, devices } from "@playwright/test";

const python = process.env.TRUTHFIT_E2E_PYTHON ?? "python";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: process.env.CI ? [["html", { open: "never" }], ["list"]] : "list",
  use: {
    baseURL: "http://127.0.0.1:3010",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: [
    {
      command: `"${python}" -m uvicorn tests.e2e.api_app:app --app-dir ../.. --host 127.0.0.1 --port 8011`,
      url: "http://127.0.0.1:8011/health",
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
      env: {
        ...process.env,
        TRUTHFIT_ENV: "test",
        TRUTHFIT_ANALYSIS_QUEUE: "background",
        TRUTHFIT_RATE_LIMIT_BACKEND: "memory",
      },
    },
    {
      command: "npx next dev --hostname 127.0.0.1 --port 3010",
      url: "http://127.0.0.1:3010",
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
      env: {
        ...process.env,
        NEXT_PUBLIC_TRUTHFIT_API_URL: "http://127.0.0.1:8011",
        NEXT_PUBLIC_TRUTHFIT_E2E_AUTH_BYPASS: "1",
        NEXT_PUBLIC_SUPABASE_URL: "https://example.supabase.co",
        NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY: "e2e-publishable-key",
      },
    },
  ],
});

import fs from "node:fs";
import path from "node:path";

import { expect, test } from "@playwright/test";

const apiUrl = "http://127.0.0.1:8011";
const sampleResume = path.resolve(process.cwd(), "../../samples/sample_resume.txt");
const sampleJob = path.resolve(process.cwd(), "../../samples/sample_job_description.txt");

test("protected API rejects a request without an access token", async ({ request }) => {
  const response = await request.get(`${apiUrl}/analysis`);
  expect(response.status()).toBe(401);
});

test("resume upload, analysis, and tracker workflow", async ({ page }) => {
  await page.goto("/jobs");
  await expect(page.getByRole("heading", { name: "Review a resume against a job" })).toBeVisible();

  await page.getByLabel("Resume file").setInputFiles(sampleResume);
  await page.getByRole("button", { name: "Parse Resume" }).click();
  await expect(page.getByText(/Resume ready:/)).toBeVisible();

  await page.getByLabel("Paste JD").fill(fs.readFileSync(sampleJob, "utf8"));
  await page.getByRole("button", { name: "Extract Requirements" }).click();
  await expect(page.getByText(/JD ready:/)).toBeVisible();

  await page.getByLabel("Role title").fill("Data Engineer");
  await page.getByLabel("Company").fill("Northstar Analytics");
  await page.getByLabel("Analysis consent").check();
  await page.getByRole("button", { name: "Run Analysis" }).click();

  await expect(page).toHaveURL(/\/analysis\/[a-f0-9]+/, { timeout: 20_000 });
  await expect(page.getByText("Overall match")).toBeVisible({ timeout: 20_000 });

  await page.getByLabel("Job status").selectOption("Applied");
  await expect(page.getByText("Saved to tracker.")).toBeVisible();

  await page.goto("/tracker");
  await expect(page.getByRole("heading", { name: "Tracked opportunities" })).toBeVisible();
  await expect(page.getByText("Data Engineer").first()).toBeVisible();
  await expect(page.getByText("Northstar Analytics").first()).toBeVisible();
});

test("privacy, terms, and password recovery are available before sign-in", async ({ page }) => {
  await page.goto("/privacy");
  await expect(page.getByRole("heading", { name: "How TruthFit handles your data" })).toBeVisible();

  await page.goto("/terms");
  await expect(page.getByRole("heading", { name: "Terms for using TruthFit" })).toBeVisible();

  await page.goto("/login");
  await page.getByRole("button", { name: "Forgot password?" }).click();
  await expect(page.getByRole("heading", { name: "Reset your password" })).toBeVisible();
});

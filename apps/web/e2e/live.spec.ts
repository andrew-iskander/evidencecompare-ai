import { test, expect } from "@playwright/test";

/**
 * Authenticated end-to-end flow against the real API (register → compare →
 * live report with evidence charts). Requires the FastAPI backend running on
 * :8000 (offline mode is fine and fast), so it is opt-in:
 *
 *   1. cd apps/api && EVIDENCE_MODE=offline LLM_MODE=offline \
 *        PIPELINE_STEP_DELAY=0 .venv/Scripts/python -m uvicorn app.main:app --port 8000
 *   2. cd apps/web && E2E_LIVE=1 npx playwright test live.spec.ts
 */
test.describe("authenticated live flow", () => {
  test.skip(!process.env.E2E_LIVE, "set E2E_LIVE=1 with the API running on :8000");

  test("register → generate report → evidence charts render", async ({ page }) => {
    const email = `e2e_${Date.now()}@example.com`;

    // Register (auto-logs-in), then wait for the success navigation so tokens are
    // persisted before we move on (otherwise navigating aborts the register fetch).
    await page.goto("/login");
    await page.getByRole("button", { name: "Register" }).click();
    await page.getByLabel(/email/i).fill(email);
    await page.getByLabel(/password/i).fill("password123");
    await Promise.all([
      page.waitForURL((u) => !u.pathname.startsWith("/login"), { timeout: 20_000 }),
      page.getByRole("button", { name: "Create account" }).click(),
    ]);

    // Fill the comparison form.
    await page.goto("/compare");
    await expect(page.getByPlaceholder("e.g. Telmisartan")).toBeVisible({
      timeout: 15_000,
    });
    await page.getByPlaceholder("e.g. Telmisartan").fill("Telmisartan");
    await page.getByPlaceholder("e.g. Valsartan").fill("Valsartan");
    await page.getByPlaceholder("e.g. Cardioprotection").fill("Cardioprotection");
    await page.getByRole("button", { name: /Generate evidence report/i }).click();

    // Land on the live report and wait for the pipeline to complete.
    await expect(page).toHaveURL(/\/reports\/[0-9a-f-]{36}/, { timeout: 30_000 });
    await expect(
      page.getByRole("heading", { name: "Side-by-side comparison" }),
    ).toBeVisible({ timeout: 45_000 });
    await expect(
      page.getByRole("heading", { name: "Evidence visualizations" }),
    ).toBeVisible({ timeout: 45_000 });

    // Charts and a verified citation are present.
    await expect(page.getByRole("heading", { name: "Evidence pyramid" })).toBeVisible();
    await expect(page.getByText(/verified citations by evidence tier/)).toBeVisible();

    // U1: the six-agent pipeline + structured trial extraction render.
    await expect(
      page.getByText("Trial-Extraction Agent", { exact: true }),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Extracted trial data" }),
    ).toBeVisible();

    // U2: living-evidence controls render on the completed report.
    await expect(page.getByText("Up to date")).toBeVisible();
    await expect(
      page.getByRole("button", { name: /Refresh evidence/i }),
    ).toBeVisible();

    // U3: the three AI-transparency layers + clinical pearls render.
    await expect(page.getByRole("heading", { name: "Clinical Summary" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Retrieved Evidence" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "AI Interpretation" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Clinical Pearls" })).toBeVisible();
  });
});

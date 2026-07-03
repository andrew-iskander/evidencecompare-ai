import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

/**
 * Accessibility smoke tests (Phase 6). Fails on WCAG 2.1 A/AA violations on the
 * key public surfaces, including the report view with all evidence charts.
 */
const TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"];

test.describe("accessibility (axe)", () => {
  test("landing page has no serious violations", async ({ page }) => {
    await page.goto("/");
    const results = await new AxeBuilder({ page }).withTags(TAGS).analyze();
    expect(results.violations).toEqual([]);
  });

  test("login page has no serious violations", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByLabel(/email/i)).toBeVisible();
    const results = await new AxeBuilder({ page }).withTags(TAGS).analyze();
    expect(results.violations).toEqual([]);
  });

  test("report view with charts has no serious violations", async ({ page }) => {
    await page.goto("/reports/demo?a=Telmisartan&b=Valsartan&topic=Cardioprotection");
    await expect(
      page.getByRole("heading", { name: "Evidence visualizations" }),
    ).toBeVisible();
    // Let the reveal/entrance animations settle so axe measures final contrast,
    // not mid-transition opacity.
    await page.getByRole("heading", { name: "References" }).waitFor();
    await page.waitForTimeout(1000);
    const results = await new AxeBuilder({ page }).withTags(TAGS).analyze();
    expect(results.violations).toEqual([]);
  });
});

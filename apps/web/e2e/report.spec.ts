import { test, expect, type Page } from "@playwright/test";
import fs from "node:fs";

const SHOT_DIR = "e2e/__screenshots__";
fs.mkdirSync(SHOT_DIR, { recursive: true });

const DEMO =
  "/reports/demo?a=Telmisartan&b=Valsartan&topic=Cardioprotection";

async function gotoDemo(page: Page, theme: "light" | "dark") {
  await page.addInitScript((t) => localStorage.setItem("theme", t), theme);
  await page.goto(DEMO);
  // The demo simulates the streaming pipeline; visuals reveal once it completes.
  await expect(
    page.getByRole("heading", { name: "Evidence visualizations" }),
  ).toBeVisible();
}

test.describe("report demo + evidence visualizations", () => {
  test("renders all four charts and captures a light screenshot", async ({ page }) => {
    await gotoDemo(page, "light");

    for (const title of [
      "Evidence timeline",
      "Evidence pyramid",
      "Confidence heatmap",
    ]) {
      await expect(page.getByRole("heading", { name: title })).toBeVisible();
    }
    await expect(
      page.getByRole("heading", { name: /Risk.benefit matrix/ }),
    ).toBeVisible();

    // Charts drew their marks / labels.
    await expect(page.getByText("verified citations by evidence tier")).toBeVisible();
    await expect(
      page.getByText("evidence-coverage map, not a clinical risk-benefit verdict"),
    ).toBeVisible();

    await page.screenshot({ path: `${SHOT_DIR}/demo-light.png`, fullPage: true });
  });

  test("captures a dark screenshot", async ({ page }) => {
    await gotoDemo(page, "dark");
    await page.screenshot({ path: `${SHOT_DIR}/demo-dark.png`, fullPage: true });
  });

  test("comparison rows expand to reveal rationale and citations", async ({ page }) => {
    await gotoDemo(page, "light");
    const row = page.getByRole("row").filter({ hasText: "Landmark CV outcome trial" });
    await row.click();
    await expect(page.getByText("Why this confidence:")).toBeVisible();
    // The expanded panel indexes the supporting citations.
    await expect(
      page.getByText("Supporting evidence:", { exact: false }),
    ).toBeVisible();
  });
});

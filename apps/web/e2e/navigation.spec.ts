import { test, expect } from "@playwright/test";

test.describe("public navigation", () => {
  test("landing page renders hero and primary CTAs", async ({ page }) => {
    await page.goto("/");
    await expect(
      page.getByRole("heading", { name: /Compare two molecules on/ }),
    ).toBeVisible();
    await expect(page.getByRole("link", { name: "Start a comparison" })).toBeVisible();
    await expect(page.getByRole("link", { name: "View sample report" })).toBeVisible();
  });

  test("Start a comparison requires sign-in (redirects to login)", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("link", { name: "Start a comparison" }).click();
    // /compare is auth-gated → unauthenticated users are sent to login with a next.
    await expect(page).toHaveURL(/\/login\?next=/);
    await expect(page.getByLabel(/email/i)).toBeVisible();
  });

  test("View sample report → rendered demo", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("link", { name: "View sample report" }).click();
    await expect(page).toHaveURL(/\/reports\/demo/);
    await expect(
      page.getByRole("heading", { name: "Side-by-side comparison" }),
    ).toBeVisible();
  });

  test("login page shows email + password fields", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();
  });
});

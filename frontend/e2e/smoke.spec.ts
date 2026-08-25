import { expect, test } from "@playwright/test";

test("today screen exposes the plan and primary workout action", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("NOZEERO / TRAINING OS")).toBeVisible();
  await expect(page.getByRole("link", { name: /START TODAY/ })).toBeVisible();
  await expect(page.getByText("28-DAY CONSISTENCY")).toBeVisible();
});

test("workout screen keeps manual mode available beside camera mode", async ({ page }) => {
  await page.goto("/workout");
  await expect(page.getByRole("button", { name: "MANUAL" })).toBeVisible();
  await expect(page.getByRole("button", { name: "CAMERA" })).toBeVisible();
  await expect(page.getByRole("button", { name: /START TIMER/ })).toBeVisible();
});

test("onboarding exposes all primary goal categories", async ({ page }) => {
  await page.goto("/onboarding");
  const goal = page.locator("#goal");
  await expect(goal.locator("option")).toHaveCount(9);
  await expect(goal.locator("option[value=core_strength]")).toHaveText("Core strength");
  await expect(page.getByText(/healthy adults 18–64/)).toBeVisible();
});

import { expect, test } from "@playwright/test";

test("结构化红旗项会阻止继续建立训练计划", async ({ page }) => {
  await page.route("**/api/v1/onboarding", (route) => route.fulfill({
    status: 201,
    contentType: "application/json",
    body: JSON.stringify({ id: "blocked-user", safety_result: { status: "BLOCKED", blockers: ["chest pain"] } }),
  }));
  await page.goto("/onboarding");
  await page.locator("#chest-pain").check({ force: true });
  await page.getByRole("button", { name: /保存并评估/ }).click();
  await expect(page.getByText(/安全筛查已阻止训练计划/)).toBeVisible();
  await expect(page).toHaveURL(/\/onboarding/);
});

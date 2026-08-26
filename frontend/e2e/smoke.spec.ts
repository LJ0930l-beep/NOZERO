import { expect, test } from "@playwright/test";

test("今日页面展示计划和主要训练入口", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("NO ZERO / 训练系统")).toBeVisible();
  await expect(page.getByRole("link", { name: /开始今天/ })).toBeVisible();
  await expect(page.getByText("28 天计划执行率")).toBeVisible();
});

test("训练页面在摄像头模式旁保留手动模式", async ({ page }) => {
  await page.goto("/workout");
  await expect(page.getByRole("button", { name: "手动" })).toBeVisible();
  await expect(page.getByRole("button", { name: "摄像头" })).toBeVisible();
  await expect(page.getByRole("button", { name: /开始计时/ })).toBeVisible();
});

test("基础资料展示全部主要目标", async ({ page }) => {
  await page.goto("/onboarding");
  const goal = page.locator("#goal");
  await expect(goal.locator("option")).toHaveCount(9);
  await expect(goal.locator("option[value=core_strength]")).toHaveText("核心力量");
  await expect(page.getByText(/18–64 岁健康成年人/)).toBeVisible();
});

import { expect, test } from "@playwright/test";

test("最小训练来自当天计划并可记录反馈", async ({ page }) => {
  await page.goto("/workout");
  await page.getByRole("button", { name: "最小" }).click();
  await expect(page.getByRole("heading", { name: "最小训练" })).toBeVisible();
  await expect(page.getByText("1/1 组已完成")).not.toBeVisible();
  await page.getByRole("button", { name: /结束训练/ }).click();
  await expect(page.getByText("训练已关闭")).toBeVisible();
  await expect(page.getByRole("button", { name: /保存反馈/ })).toBeVisible();
});

import { expect, test } from "@playwright/test";

const workout = {
  date: "2026-08-27", day_index: 0, title: "力量 + 体能", focus: "深蹲 + 核心", duration_minutes: 16, kind: "TRAINING",
  blocks: [{ exercise_id: "squat_bodyweight", name: "自重深蹲", sets: 2, reps: 10, duration_seconds: null, rest_seconds: 60, intent: "全脚掌保持稳定" }],
  short_workout: [{ exercise_id: "squat_bodyweight", name: "自重深蹲", sets: 1, reps: 8, duration_seconds: null, rest_seconds: 30, intent: "全脚掌保持稳定" }],
  minimum_workout: [{ exercise_id: "squat_bodyweight", name: "自重深蹲", sets: 1, reps: 8, duration_seconds: null, rest_seconds: 20, intent: "全脚掌保持稳定", minimum: true }],
};

test("完整用户流可以从基础资料走到反馈", async ({ page }) => {
  await page.route("**/api/v1/onboarding", (route) => route.fulfill({ status: 201, contentType: "application/json", body: JSON.stringify({ id: "e2e-user", safety_result: { status: "SAFE", blockers: [] } }) }));
  await page.route("**/api/v1/assessments", (route) => route.fulfill({ status: 201, contentType: "application/json", body: JSON.stringify({ id: "assessment-1", user_id: "e2e-user", assessed_at: "2026-08-27T00:00:00Z", dimensions: { upper_body: "F2", lower_body: "F2", core: "F2", cardio: "F2", mobility: "F2" }, raw_inputs: {} }) }));
  await page.route("**/api/v1/plans", (route) => route.fulfill({ status: 201, contentType: "application/json", body: JSON.stringify({ id: "cycle-1", user_id: "e2e-user", start_date: workout.date, end_date: workout.date, goal: "fat_loss", secondary_focus: "abs", weekly_plan: [workout], weekly_cardio_target_minutes: 90, cardio_minutes_completed: 0 }) }));
  await page.route("**/api/v1/dashboard*", (route) => route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ user: { id: "e2e-user", age: 30, training_experience: "beginner", session_duration_minutes: 20, equipment_mode: "ZERO", primary_goal: "fat_loss", secondary_focus: "abs", safety_status: "SAFE" }, current_streak: 1, longest_streak: 1, consistency: { "7": { completed: 1, planned: 7, percentage: 14.3 }, "28": { completed: 1, planned: 28, percentage: 3.6 }, "90": { completed: 1, planned: 90, percentage: 1.1 } }, total_training_minutes: 16, fitness_levels: { core: "F2" }, assessment_history: [], performance_change: {}, achievements: [], discipline_level: "D1 起步", xp: 100, next_workout: workout, plan_adherence: { completed: 1, planned: 1, percentage: 100 }, aerobic_dose: { target_minutes: 90, completed_minutes: 0, percentage: 0 } }) }));
  await page.route("**/api/v1/workouts/today*", (route) => route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(workout) }));
  await page.route("**/api/v1/workouts/feedback", (route) => route.fulfill({ status: 201, contentType: "application/json", body: JSON.stringify({ id: "session-1", workout_date: workout.date, status: "FULL", xp: 100, next_recommendation: "继续计划", recovery_status: "NORMAL" }) }));

  await page.goto("/onboarding");
  await page.getByRole("button", { name: /保存并评估/ }).click();
  await expect(page).toHaveURL(/\/assessment/);
  await page.getByRole("button", { name: /生成四周计划/ }).click();
  await expect(page).toHaveURL(/\/$/);
  await expect(page.getByText("28 天计划执行率")).toBeVisible();
  await page.getByRole("link", { name: /开始训练/ }).click();
  await expect(page).toHaveURL(/\/workout/);
  await page.getByRole("button", { name: /结束训练/ }).click();
  await page.getByRole("button", { name: /保存反馈/ }).click();
  await expect(page.getByText(/已记录为 FULL/)).toBeVisible();
});

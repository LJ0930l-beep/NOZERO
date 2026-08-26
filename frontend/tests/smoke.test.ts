import { describe, expect, it } from "vitest";

import { DEMO_DASHBOARD, DEMO_WORKOUT } from "../lib/api";

describe("NO ZERO 前端契约", () => {
  it("keeps the demo plan and dashboard aligned", () => {
    expect(DEMO_WORKOUT.minimum_workout.length).toBeGreaterThan(0);
    expect(DEMO_WORKOUT.short_workout.length).toBeGreaterThanOrEqual(DEMO_WORKOUT.minimum_workout.length);
    expect(DEMO_DASHBOARD.next_workout?.date).toBe(DEMO_WORKOUT.date);
    expect(DEMO_DASHBOARD.consistency["28"].percentage).toBe(86);
  });
});

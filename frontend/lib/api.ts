import type { Dashboard, DailyWorkout } from "./types";

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");
const USER_ID_KEY = "nozero.userId";
const LEGACY_USER_ID_KEY = "nozeero.userId";

export function localDateString(value = new Date()): string {
  const offset = value.getTimezoneOffset() * 60_000;
  return new Date(value.getTime() - offset).toISOString().slice(0, 10);
}

export async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options?.headers ?? {}) },
    cache: "no-store",
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail ?? `Request failed with ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function storeUserId(userId: string): void {
  if (typeof window !== "undefined") window.localStorage.setItem(USER_ID_KEY, userId);
}

export function readUserId(): string | null {
  if (typeof window === "undefined") return null;
  const userId = window.localStorage.getItem(USER_ID_KEY);
  if (userId) return userId;
  const legacyUserId = window.localStorage.getItem(LEGACY_USER_ID_KEY);
  if (legacyUserId) window.localStorage.setItem(USER_ID_KEY, legacyUserId);
  return legacyUserId;
}

export const DEMO_WORKOUT: DailyWorkout = {
  date: localDateString(),
  day_index: 23,
  title: "力量 + 体能",
  focus: "深蹲 + 核心",
  duration_minutes: 16,
  kind: "TRAINING",
  blocks: [
    { exercise_id: "squat_bodyweight", name: "自重深蹲", sets: 3, reps: 12, duration_seconds: null, rest_seconds: 60, intent: "全脚掌保持稳定" },
    { exercise_id: "push_knee", name: "跪姿俯卧撑", sets: 3, reps: 8, duration_seconds: null, rest_seconds: 60, intent: "收紧肋骨" },
    { exercise_id: "core_plank", name: "平板支撑", sets: 2, reps: null, duration_seconds: 30, rest_seconds: 30, intent: "保持呼吸，不塌腰" },
  ],
  short_workout: [
    { exercise_id: "squat_bodyweight", name: "自重深蹲", sets: 2, reps: 10, duration_seconds: null, rest_seconds: 30, intent: "全脚掌保持稳定" },
    { exercise_id: "push_knee", name: "跪姿俯卧撑", sets: 2, reps: 8, duration_seconds: null, rest_seconds: 30, intent: "收紧肋骨" },
    { exercise_id: "core_plank", name: "平板支撑", sets: 1, reps: null, duration_seconds: 25, rest_seconds: 30, intent: "保持呼吸，不塌腰" },
  ],
  minimum_workout: [
    { exercise_id: "squat_bodyweight", name: "自重深蹲", sets: 1, reps: 8, duration_seconds: null, rest_seconds: 20, intent: "全脚掌保持稳定", minimum: true },
    { exercise_id: "core_plank", name: "平板支撑", sets: 1, reps: null, duration_seconds: 20, rest_seconds: 20, intent: "保持呼吸，不塌腰", minimum: true },
  ],
};

export const DEMO_DASHBOARD: Dashboard = {
  user: { id: "demo", age: 31, training_experience: "beginner", session_duration_minutes: 20, equipment_mode: "ZERO", primary_goal: "fat_loss", secondary_focus: "abs", safety_status: "SAFE" },
  current_streak: 8,
  longest_streak: 14,
  consistency: { "28": { completed: 24, planned: 28, percentage: 86 } },
  total_training_minutes: 312,
  fitness_levels: { upper_body: "F2", lower_body: "F3", core: "F2", cardio: "F2", mobility: "F2" },
  assessment_history: [],
  performance_change: {},
  achievements: ["first_session", "seven_day_streak"],
  discipline_level: "D3 专注",
  xp: 1240,
  next_workout: DEMO_WORKOUT,
  plan_adherence: { completed: 24, planned: 28, percentage: 86, recovery_days: 4, zero_days: 0 },
  activity_consistency: { "28": { completed: 24, planned: 28, percentage: 86 } },
  aerobic_dose: { target_minutes: 90, completed_minutes: 42, percentage: 46.7 },
};

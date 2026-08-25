import type { Dashboard, DailyWorkout } from "./types";

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");

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
  if (typeof window !== "undefined") window.localStorage.setItem("nozeero.userId", userId);
}

export function readUserId(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem("nozeero.userId");
}

export const DEMO_WORKOUT: DailyWorkout = {
  date: new Date().toISOString().slice(0, 10),
  day_index: 23,
  title: "Strength + conditioning",
  focus: "Squat + Core",
  duration_minutes: 16,
  kind: "TRAINING",
  blocks: [
    { exercise_id: "squat_bodyweight", name: "Bodyweight Squat", sets: 3, reps: 12, duration_seconds: null, rest_seconds: 60, intent: "Keep the whole foot grounded" },
    { exercise_id: "push_knee", name: "Knee Push-up", sets: 3, reps: 8, duration_seconds: null, rest_seconds: 60, intent: "Brace the ribs" },
    { exercise_id: "core_plank", name: "Plank", sets: 2, reps: null, duration_seconds: 30, rest_seconds: 30, intent: "Breathe behind the brace" },
  ],
  short_workout: [
    { exercise_id: "squat_bodyweight", name: "Bodyweight Squat", sets: 2, reps: 10, duration_seconds: null, rest_seconds: 30, intent: "Keep the whole foot grounded" },
    { exercise_id: "push_knee", name: "Knee Push-up", sets: 2, reps: 8, duration_seconds: null, rest_seconds: 30, intent: "Brace the ribs" },
    { exercise_id: "core_plank", name: "Plank", sets: 1, reps: null, duration_seconds: 25, rest_seconds: 30, intent: "Breathe behind the brace" },
  ],
  minimum_workout: [
    { exercise_id: "squat_bodyweight", name: "Bodyweight Squat", sets: 1, reps: 8, duration_seconds: null, rest_seconds: 20, intent: "Keep the whole foot grounded", minimum: true },
    { exercise_id: "core_plank", name: "Plank", sets: 1, reps: null, duration_seconds: 20, rest_seconds: 20, intent: "Breathe behind the brace", minimum: true },
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
  discipline_level: "D3 Focused",
  xp: 1240,
  next_workout: DEMO_WORKOUT,
};

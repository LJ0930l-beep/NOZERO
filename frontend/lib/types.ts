export type WorkoutBlock = {
  exercise_id: string;
  name: string;
  sets: number;
  reps: number | null;
  duration_seconds: number | null;
  rest_seconds: number;
  intent: string;
  minimum?: boolean;
};

export type DailyWorkout = {
  date: string;
  day_index: number;
  title: string;
  focus: string;
  duration_minutes: number;
  kind: "TRAINING" | "RECOVERY";
  blocks: WorkoutBlock[];
  short_workout: WorkoutBlock[];
  minimum_workout: WorkoutBlock[];
};

export type User = {
  id: string;
  age: number;
  training_experience: string;
  session_duration_minutes: number;
  equipment_mode: string;
  primary_goal: string;
  secondary_focus: string;
  safety_status: string;
};

export type Dashboard = {
  user: User;
  current_streak: number;
  longest_streak: number;
  consistency: Record<string, { completed: number; planned: number; percentage: number }>;
  total_training_minutes: number;
  fitness_levels: Record<string, string>;
  assessment_history: { id: string; user_id: string; assessed_at: string; dimensions: Record<string, string>; raw_inputs: Record<string, number> }[];
  performance_change: Record<string, { before: string; after: string; delta: number }>;
  achievements: string[];
  discipline_level: string;
  xp: number;
  next_workout: DailyWorkout | null;
};

export type CoachResponse = {
  source: "ollama" | "fallback";
  fatigue: "low" | "moderate" | "high" | "unknown";
  motivation: "low" | "moderate" | "high" | "unknown";
  time_available_minutes: number | null;
  recommendation: "normal" | "short" | "minimum" | "recovery" | "stop";
  reason: string;
  message: string;
};

export type WellnessSummary = {
  latest: {
    log_date: string;
    body_weight_kg: number | null;
    protein_awareness: boolean | null;
    hydration_glasses: number | null;
    fruit_vegetable_servings: number | null;
    steps: number | null;
    daily_movement_minutes: number | null;
    sedentary_minutes: number | null;
    notes: string;
  } | null;
  body_weight_trend: { date: string; weight_kg: number }[];
  averages: Record<string, number>;
};

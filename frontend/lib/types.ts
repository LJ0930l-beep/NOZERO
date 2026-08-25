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
  discipline_level: string;
  xp: number;
  next_workout: DailyWorkout | null;
};

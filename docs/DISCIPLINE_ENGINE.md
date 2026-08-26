# Discipline Engine

Daily states are `FULL`, `MINIMUM`, `RECOVERY`, and `ZERO`. The first three are execution successes. XP is 100/30/20/0 by default. Streaks count consecutive successful calendar dates, and planned recovery is included. Consistency is reported over 7, 28, and 90-day windows so one missed day does not erase long-term progress.

Plan Adherence is the core execution metric: successful execution of due plan days divided by due plan days. A planned recovery day is settled as `RECOVERY` even without a session row; a missed training day or `ZERO` is a failure. Activity consistency remains a separate actual-movement view over 7, 28, and 90 local calendar days.

Discipline level is independent from fitness level: D1 Starter, D2 Consistent, D3 Focused, D4 Disciplined, D5 Unbreakable. The product uses these as feedback signals, not as a moral judgment or the only success metric.

Small local achievements are derived from the same session ledger: first session, rescue kept, recovery is training, seven-day streak, and one-thousand XP. They are display-only and cannot alter safety, recovery, progression, or plan volume. Weekly Review combines completed sessions, load signals, recovery feedback, and assessment history to report both execution change and fitness progress before making a conservative next-week recommendation.

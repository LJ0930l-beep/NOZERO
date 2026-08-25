"""Initialize the local NOZEERO database with versioned exercise seed data."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

def main() -> None:
    from backend.app.core.config import settings
    from backend.app.db.database import Database
    from backend.app.repositories.sqlite_repository import SQLiteRepository

    exercises_path = ROOT / "data" / "exercises" / "exercises.json"
    exercises = json.loads(exercises_path.read_text(encoding="utf-8"))
    repository = SQLiteRepository(Database(settings.database_url))
    repository.initialize()
    count = repository.seed_exercises(exercises)
    print(f"Seeded {count} exercises into {repository.database.database_path}")


if __name__ == "__main__":
    main()

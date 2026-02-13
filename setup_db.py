"""Initialize the database and seed with default data."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.db.database import init_db, SessionLocal
from src.db import crud


def seed():
    db = SessionLocal()
    try:
        if not crud.get_user(db, "admin"):
            crud.create_user(db, "admin", "Administrator", "admin")
        if not crud.get_user(db, "reviewer1"):
            crud.create_user(db, "reviewer1", "QA Reviewer", "reviewer")
        if not crud.get_project_by_name(db, "Demo Project"):
            crud.create_project(db, "Demo Project", "Sample project for demonstration")
        print("Database seeded successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Database tables created.")
    seed()

from pathlib import Path
import sqlite3

from import_gold_data import main as import_gold_data


ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "avc_explorer.db"
SCHEMA_PATH = ROOT / "database" / "schema.sql"


def initialize_database():
    if DB_PATH.exists():
        print(f"Database already exists: {DB_PATH}")
        return

    print("Database not found. Creating it...")

    schema = SCHEMA_PATH.read_text(encoding="utf-8")

    connection = sqlite3.connect(DB_PATH)

    try:
        connection.executescript(schema)
        connection.commit()
    finally:
        connection.close()

    print("Database schema created.")

    import_gold_data()

    print("Database initialization complete.")


if __name__ == "__main__":
    initialize_database()
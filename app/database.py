import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = ROOT / "avc_explorer.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection
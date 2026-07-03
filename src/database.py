"""
SQLite persistence layer.
Keeps the app usable offline / without re-importing a CSV every launch.
"""

import sqlite3
from pathlib import Path
import pandas as pd

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "cms.db"


class Database:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))

    def save_customers(self, df: pd.DataFrame, table: str = "customers"):
        df.to_sql(table, self.conn, if_exists="replace", index=False)

    def load_customers(self, table: str = "customers") -> pd.DataFrame:
        try:
            return pd.read_sql(f"SELECT * FROM {table}", self.conn)
        except Exception:
            return pd.DataFrame()

    def table_exists(self, table: str) -> bool:
        cur = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
        )
        return cur.fetchone() is not None

    def close(self):
        self.conn.close()

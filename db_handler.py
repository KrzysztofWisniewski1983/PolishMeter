"""Full database handler implementation."""

import sqlite3
from utils.utils import Indicator
from dataclasses import asdict
from typing import List, Dict, Any

DESCRIPTION = """

NAME:
    database handler - A module to handle database operations.
DESCRIPTION:
    This module provides the following functionalities:
    Initialization (connecting to the database, creating tables if they do not exist),
    Saving data (list of dictionaries -> INSERT),
    Reading data (SELECT),
    Updating records (UPDATE),
    Deleting records (DELETE),
    Closing the connection.
"""

COLUMNS = {
    "key": "TEXT PRIMARY KEY",
    "name": "TEXT",
    "value": "INTEGER",
    "unit": "TEXT",
    "source": "TEXT",
    "last_update_date": "TEXT",
    "last_download_date": "TEXT",
    "group_name": "TEXT",
    "category": "TEXT",
    "chart_path": "TEXT",
}

class DatabaseHandler:
    """Class to handle database operations."""
    def __init__(self, db_path: str = "data.db"):
        """Inicjalizacja połączenia z bazą danych."""
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # pozwala zwracać dane jako słowniki
        self.cursor = self.conn.cursor()

    def create_table(self, table_name: str, columns: Dict[str, str]):
        """
        Tworzy tabelę, jeśli nie istnieje.
        columns: np. {"name": "TEXT", "value": "INTEGER", "unit": "TEXT"}
        """
        cols = ", ".join([f"{col} {dtype}" for col, dtype in columns.items()])
        # Dodaj UNIQUE(name), wartości w kolumnie name muszą być unikalne
        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({cols}, UNIQUE(name))"
        self.cursor.execute(query)
        self.conn.commit()

    def save_data(self, table_name: str, data: List[Dict[str, Any]]):
        """
        Zapisuje listę słowników do tabeli.
        """
        if not data:
            return
        columns = ", ".join(data[0].keys())
        placeholders = ", ".join(["?"] * len(data[0]))
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        values = [tuple(row.values()) for row in data]
        self.cursor.executemany(query, values)
        self.conn.commit()

    def read_data(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Odczytuje wszystkie dane z tabeli i zwraca jako listę słowników.
        """
        query = f"SELECT * FROM {table_name}"
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]

    def update_data(self, table_name: str, set_values: Dict[str, Any], condition: str):
        """
        Aktualizuje dane w tabeli.
        set_values: np. {"value": 12345}
        condition: np. "name='total_vehicles_ytd'"
        """
        set_clause = ", ".join([f"{col} = ?" for col in set_values.keys()])
        query = f"UPDATE {table_name} SET {set_clause} WHERE {condition}"
        self.cursor.execute(query, tuple(set_values.values()))
        self.conn.commit()

    def delete_data(self, table_name: str, condition: str):
        """
        Usuwa dane z tabeli na podstawie warunku.
        """
        query = f"DELETE FROM {table_name} WHERE {condition}"
        self.cursor.execute(query)
        self.conn.commit()

    def save_or_update(self, table_name: str, data: Indicator):
        """Insert a new record or update an existing one."""

        data = asdict(data)

        columns = list(data.keys())
        placeholders = ", ".join(["?"] * len(columns))
        columns_sql = ", ".join(columns)

        update_clause = ", ".join(
            f"{col}=excluded.{col}"
            for col in columns
            if col != "name"
        )

        query = f"""
            INSERT INTO {table_name} ({columns_sql})
            VALUES ({placeholders})
            ON CONFLICT(name) DO UPDATE SET
            {update_clause}
        """

        self.cursor.execute(query, tuple(data[col] for col in columns))
        row = self.cursor.execute(
            f"SELECT key FROM {table_name} WHERE name = ?", (data["name"],)
        ).fetchone()
        print("Zapisano rekord, key:", row["key"])
        self.conn.commit()

    def close(self):
        """Zamyka połączenie z bazą danych."""
        self.conn.close()

def initialize_database(db_path, table_name):
    """Tworzy tabelę, jeśli jeszcze nie istnieje."""

    db = DatabaseHandler(db_path)

    try:
        query = """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name = ?
        """

        db.cursor.execute(query, (table_name,))
        result = db.cursor.fetchone()

        if result is None:
            print(f"Tabela '{table_name}' nie istnieje. Tworzę...")
            db.create_table(table_name, COLUMNS)
            print("Tabela została utworzona.")
        else:
            print(f"Tabela '{table_name}' już istnieje.")

    finally:
        db.close()

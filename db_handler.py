"""SQLite database handler for storing and updating statistical indicators.

This module provides the `DatabaseHandler` class and the `initialize_database`
helper function for managing the database lifecycle, including table creation,
CRUD operations, and upserting `Indicator` objects.
"""

import sqlite3
from utils.utils import Indicator
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
    "value": "NUMERIC",
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
        """Initialize the database connection."""
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # Return rows as dictionary-like objects
        self.cursor = self.conn.cursor()

    def create_table(self, table_name: str, columns: Dict[str, str]):
        """Create a table if it does not already exist.

        Args:
            table_name: Name of the database table.
            columns: Mapping of column names to SQLite data types.
        """     
        cols = ", ".join([f"{col} {dtype}" for col, dtype in columns.items()])
        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({cols})"
        self.cursor.execute(query)
        self.conn.commit()

    def save_data(self, table_name: str, data: List[Dict[str, Any]]):
        """Insert a list of dictionaries into the specified table."""
        if not data:
            return
        columns = ", ".join(data[0].keys())
        placeholders = ", ".join(["?"] * len(data[0]))
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        values = [tuple(row.values()) for row in data]
        self.cursor.executemany(query, values)
        self.conn.commit()

    def read_data(self, table_name: str) -> List[Dict[str, Any]]:
        """Read all records from the table and return them as a list of dicts."""
        query = f"SELECT * FROM {table_name}"
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]

    def update_data(self, table_name: str, set_values: Dict[str, Any], condition: str):
        """Update records matching the given SQL condition."""
        set_clause = ", ".join([f"{col} = ?" for col in set_values.keys()])
        query = f"UPDATE {table_name} SET {set_clause} WHERE {condition}"
        self.cursor.execute(query, tuple(set_values.values()))
        self.conn.commit()

    def delete_data(self, table_name: str, condition: str):
        """Delete records matching the given SQL condition."""
        query = f"DELETE FROM {table_name} WHERE {condition}"
        self.cursor.execute(query)
        self.conn.commit()

    def save_or_update(self, table_name: str, data: Indicator):
        """Insert a new Indicator record or update an existing one on key conflict."""
        record = data.to_dict()

        columns = list(record.keys())
        placeholders = ", ".join(["?"] * len(columns))
        columns_sql = ", ".join(columns)

        update_clause = ", ".join(
            f"{col}=excluded.{col}"
            for col in columns
            if col != "key"
        )

        query = f"""
            INSERT INTO {table_name} ({columns_sql})
            VALUES ({placeholders})
            ON CONFLICT(key) DO UPDATE SET
            {update_clause}
        """

        self.cursor.execute(query, tuple(record[col] for col in columns))
        self.conn.commit()
        print("Zapisano rekord, key:", record["key"])


    def close(self):
        """Zamyka połączenie z bazą danych."""
        self.conn.close()

def initialize_database(db_path, table_name):
    """Create the target database table if it does not exist yet."""
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
            print(f"Table '{table_name}' does not exist. Creating...")
            db.create_table(table_name, COLUMNS)
            print("Table created successfully.")
        else:
            print(f"Table '{table_name}' already exists.")

    finally:
        db.close()

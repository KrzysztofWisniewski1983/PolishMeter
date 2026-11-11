import sqlite3
import pytest
from pathlib import Path

DATABASE_PATH = "data/data.db"

@pytest.fixture
def db_connection():
    db_path = Path(DATABASE_PATH).resolve()

    connection = sqlite3.connect(
        f"file:{db_path}?mode=ro",
        uri=True
    )

    yield connection

    connection.close()

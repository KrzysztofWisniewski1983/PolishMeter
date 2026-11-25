"""PolishMeter project shared pytest fixtures."""

import json
import sqlite3
import pytest
from pathlib import Path
from config.settings import settings
from db_handler import DatabaseHandler, COLUMNS


@pytest.fixture(scope="session")
def test_resources():
    base_path = Path(__file__).resolve().parent.parent

    config_path = base_path / "config" / settings.gus_bdl_indicators_file
    with config_path.open(encoding="utf-8") as file:
        gus_config = json.load(file)
    
    test_data_path = base_path / "test_data" / "gus_test_data.json"
    with test_data_path.open(encoding="utf-8") as file:
        gus_test_data = json.load(file)

    response_gus_api = {
        "results": [{
            "id": "000000000000",
            "name": "POLSKA",
            "values": [
                {"year": "2023", "val": 216027, "attrId": 1},
                {"year": "2024", "val": 194246, "attrId": 1},
                {"year": "2025", "val": 194037, "attrId": 1},
            ],
        }]
        }

    return {
        "gus_config": gus_config,
        "gus_test_data": gus_test_data,
        "response_gus_api": response_gus_api
    }


@pytest.fixture
def test_db(tmp_path_factory):
    db_path = db_path = Path(settings.database_path).resolve()

    handler = DatabaseHandler(str(db_path))
    handler.create_table("indicators", COLUMNS)

    yield handler

    handler.close()


# @pytest.fixture
# def db_connection():
#     db_path = Path(DATABASE_PATH).resolve()

#     connection = sqlite3.connect(
#         f"file:{db_path}?mode=ro",
#         uri=True
#     )

#     yield connection

#     connection.close()

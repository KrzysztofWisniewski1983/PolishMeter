"""PolishMeter project integration tests.

Regarding tests with db, each test uses the same temporary SQLite database but independently
prepares and removes its test records.
Tests cover inserting, updating, and deleting indicator records.
"""

import pytest

from utils.utils import Indicator
from db_handler import DatabaseHandler, COLUMNS


@pytest.fixture(scope="module")
def db(tmp_path_factory):
    db_path = tmp_path_factory.mktemp("database") / "test.db"

    handler = DatabaseHandler(str(db_path))
    handler.create_table("indicators", COLUMNS)

    yield handler

    handler.close()


@pytest.fixture
def indicator_data():
    return Indicator(
        name="test_001",
        value=12345,
        unit="osoby",
        source="GUS",
        last_update_date="2026-10-30",
        last_download_date="2026-10-30",
        group_name="Test",
        category="Test category",
        chart_path=None,
    )


@pytest.fixture
def updated_indicator_data(indicator_data):
    return Indicator(
        **{
            **indicator_data.__dict__,
            "value": 200,
            "last_update_date": "2026-10-31",
        }
    )


def test_db_save_or_update_inserts_new_record(db, indicator_data):
    db.save_or_update("indicators", indicator_data)

    records = db.read_data("indicators")

    assert len(records) == 1
    #assert records[0]["key"] == indicator_data.key
    assert records[0]["key"] is not None
    assert records[0]["name"] == indicator_data.name
    assert records[0]["value"] == indicator_data.value

    #db.delete_data("indicators", f"key = '{indicator_data.key}'")
    record_key = records[0]["key"]
    db.delete_data("indicators", f"key = {record_key}")


def test_db_save_or_update_updates_existing_record(
    db, indicator_data, updated_indicator_data
):
    db.save_or_update("indicators", indicator_data)
    db.save_or_update("indicators", updated_indicator_data)

    records = db.read_data("indicators")

    assert len(records) == 1
    assert records[0]["name"] == indicator_data.name
    assert records[0]["value"] == updated_indicator_data.value
    assert records[0]["last_update_date"] == updated_indicator_data.last_update_date

    #db.delete_data("indicators", f"key = '{indicator_data.key}'")
    record_key = records[0]["key"]
    db.delete_data("indicators", f"key = {record_key}")


# def test_db_delete_data_removes_existing_record(db, indicator_data):
#     db.save_or_update("indicators", indicator_data)

#     db.delete_data("indicators", f"key = '{indicator_data.key}'")

#     records = db.read_data("indicators")

#     assert len(records) == 0

def test_db_delete_data_removes_existing_record(db, indicator_data):
    db.save_or_update("indicators", indicator_data)

    records = db.read_data("indicators")
    record_key = records[0]["key"]

    db.delete_data("indicators", f"key = {record_key}")

    records = db.read_data("indicators")

    assert len(records) == 0

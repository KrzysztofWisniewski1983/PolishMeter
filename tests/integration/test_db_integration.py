"""PolishMeter project database integration tests.

Tests use a temporary SQLite database to verify schema creation,
inserting, updating (upsert without duplicates), reading, and deleting
statistical indicator records across all data sources.
"""

import pytest

from utils.utils import Indicator


@pytest.fixture
def indicator_data():
    return Indicator(
        key="T1",
        name="Test indicator",
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
            "last_download_date": "2026-10-31",
        }
    )


def test_db_save_or_update_inserts_new_record(test_db, indicator_data):
    """Verify that save_or_update inserts a new indicator record into the database."""
    test_db.save_or_update("indicators", indicator_data)

    records = test_db.read_data("indicators")

    assert len(records) == 1
    assert records[0]["key"] == indicator_data.key
    assert records[0]["name"] == indicator_data.name
    assert records[0]["value"] == indicator_data.value


def test_db_save_or_update_updates_existing_record(
    test_db, indicator_data, updated_indicator_data
):
    """Verify that save_or_update updates an existing record by key without creating duplicates."""
    test_db.save_or_update("indicators", indicator_data)
    test_db.save_or_update("indicators", updated_indicator_data)

    records = test_db.read_data("indicators")

    assert len(records) == 1
    assert records[0]["key"] == indicator_data.key
    assert records[0]["value"] == updated_indicator_data.value
    assert records[0]["last_update_date"] == updated_indicator_data.last_update_date
    assert records[0]["last_download_date"] == updated_indicator_data.last_download_date


def test_db_delete_data_removes_existing_record(test_db, indicator_data):
    """Verify that delete_data removes an existing indicator record matching the condition."""
    test_db.save_or_update("indicators", indicator_data)

    records = test_db.read_data("indicators")
    assert len(records) == 1

    test_db.delete_data("indicators", f"key = '{indicator_data.key}'")

    records = test_db.read_data("indicators")

    assert len(records) == 0

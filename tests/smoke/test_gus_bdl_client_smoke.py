"""PolishMeter project smoke tests for basic application and data source checks."""

from tests.helpers.helpers import read_db_value

INDICATOR_NAME = "Bezrobocie w 2025 roku"

def test_population_value(db_connection):
    expected_value = read_db_value(
        db_connection,
        INDICATOR_NAME
    )

    assert expected_value is not None

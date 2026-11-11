"""PolishMeter project E2E tests."""

from config.settings import settings
from tests.helpers.helpers import read_db_value

INDICATOR_NAME = "Bezrobocie w 2025 roku"

def test_unemployment_value_matches_database(
    db_connection,
    page
    ):

    page.goto(settings.web_page)

    # Act – odczyt wartości z bazy
    expected_value = read_db_value(
        db_connection,
        INDICATOR_NAME
    )

    row = page.locator("tr").filter(
        has_text=INDICATOR_NAME
    )
    actual_value = row.locator("td").nth(1).inner_text()

    assert actual_value == str(expected_value)

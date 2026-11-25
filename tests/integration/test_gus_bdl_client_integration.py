"""PolishMeter project integration tests for the GUS BDL client and pipeline.

Tests use mocked HTTP responses from the GUS BDL API to verify data
fetching, parsing, normalization into database-ready indicator records,
and chart generation without persisting to the production database.
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock
from clients.gus_bdl_client import GusClient


def test_gus_client_generates_indicators_for_db(tmp_path, test_resources):
    # Arrange
    response_gus_api = test_resources["response_gus_api"]
    
    indicators_config = {"459121": test_resources["gus_config"]["459121"] }

    mock_date_provider = MagicMock()
    mock_http_client = MagicMock()
    mock_date_provider.get_current_datetime.return_value = datetime(2026, 11, 20, 12, 0, 0)
    mock_http_client.request_with_retry.return_value.json.return_value = response_gus_api

    gus = GusClient(
            http_client=mock_http_client,
            date_provider=mock_date_provider,
            indicators_config=indicators_config,
            charts_dir=tmp_path
        )

    #Act
    gus.get_gus_bdl_data()
    gus.create_chart_for_gus_bdl_data()
    indicators = gus.generate_indicators_for_gus_bdl_data()

    #Assert
    assert len(indicators) == 2

    # numeric_indicator = indicators[0]
    # chart_indicator = indicators[1]

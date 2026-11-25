"""PolishMeter project unit tests."""

from unittest.mock import Mock
from clients.gus_bdl_client import GusClient


def test_get_variable_data_url(tmp_path):
    """Verify that the variable data URL is built with unit-level=0."""
    client = GusClient(
        http_client=None,
        date_provider=None,
        indicators_config={},
        charts_dir=tmp_path
    )

    url = client._get_variable_data_url("459121")

    assert url == (
        "https://bdl.stat.gov.pl/api/v1/data/by-variable/"
        "459121?format=json&unit-level=0"
    )


def test_get_gus_bdl_data(tmp_path):
    """Verify that get_gus_bdl_data parses national-level years and values correctly."""
    indicators_config = {
        "459121": {
            "name": "Bezrobocie",
        }
    }

    client = GusClient(
        http_client=Mock(),
        date_provider=Mock(),
        indicators_config=indicators_config,
        charts_dir=tmp_path
    )

    data_response = Mock()
    data_response.json.return_value = {
        "results": [
            {
                "id": "000000000000",
                "values": [
                    {"year": 2023, "val": 12345}
                ],
            }
        ]
    }

    client._get_response = Mock(return_value=data_response)

    client.get_gus_bdl_data()

    assert client.data_dict["459121"]["years"] == ["2023"]
    assert client.data_dict["459121"]["values"] == [12345]


def test_generate_indicators_for_gus_bdl_data(tmp_path):
    """Verify that Indicator objects are generated with latest year and updated date fields."""
    indicators_config = {
        "459121": {
            "key": "P1",
            "name": "Bezrobocie",
            "unit": "osoby",
            "category": "Rynek pracy",
        }
    }

    client = GusClient(
        http_client=Mock(),
        date_provider=Mock(),
        indicators_config=indicators_config,
        charts_dir=tmp_path,
    )
    client._get_download_date = Mock(return_value="2026-11-17 20:00:00")
    client.data_dict["459121"]["years"] = ["2024", "2025"]
    client.data_dict["459121"]["values"] = [200000, 194037]

    indicators = client.generate_indicators_for_gus_bdl_data()

    assert len(indicators) == 1
    assert indicators[0].key == "P1"
    assert indicators[0].value == 194037
    assert indicators[0].last_update_date == "2025"
    assert indicators[0].last_download_date == "2026-11-17 20:00:00"

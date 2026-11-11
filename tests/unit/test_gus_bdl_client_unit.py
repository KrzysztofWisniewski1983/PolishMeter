"""PolishMeter project unit tests."""

from unittest.mock import Mock
from clients.gus_bdl_client import GusClient


def test_get_variable_data_url(tmp_path):
    client = GusClient(
        http_client=None,
        date_provider=None,
        indicators_config={},
        charts_dir=tmp_path
    )

    url = client._get_variable_data_url("459121", 2024)

    assert url == (
        "https://bdl.stat.gov.pl/api/v1/data/by-variable/"
        "459121?format=json&unit-id=0&year=2024&page-size="
        f"{client.PAGE_SIZE}"
    )

def test_get_gus_bdl_data(tmp_path):
    # Arrange — przygotowanie danych testowych
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

    client._get_variable_url = Mock(return_value="metadata_url")
    client._get_variable_data_url = Mock(return_value="data_url")

    metadata_response = Mock()
    metadata_response.json.return_value = {
        "years": [2023]
    }

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

    client._get_response = Mock(
        side_effect=[metadata_response, data_response]
    )

    # Act — uruchomienie testowanej metody
    client.get_gus_bdl_data()

    # Assert — sprawdzenie rezultatu
    assert client.data_dict["459121"]["years"] == ["2023"]
    assert client.data_dict["459121"]["values"] == [12345]

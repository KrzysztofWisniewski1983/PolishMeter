"""PolishMeter project tests for the GUS BDL API client."""

import json
from pathlib import Path

import pytest
import requests
from jsonschema import validate

from config.settings import settings

CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "gus_bdl_indicators.json"

with CONFIG_PATH.open(encoding="utf-8") as file:
    config = json.load(file)

VARIABLE_IDS = list(config.keys())

VARIABLE_ID = "459121"
VARIABLE_ID_FAKE = "999999999999999"
NATIONAL_LEVEL_ID = "000000000000"


@pytest.fixture(scope="session")
def gus_response_schema():
    schema_path = (
        Path(__file__).parent
        / "schemas"
        / "gus_bdl_data_schema.json"
    )

    with open(schema_path, encoding="utf-8") as file:
        return json.load(file)


@pytest.mark.parametrize("variable_id", VARIABLE_IDS)
def test_gus_bdl_variable_metadata(variable_id):
    url = (
        f"{settings.gus_bdl_api_url}variables/"
        f"{variable_id}?format=json"
    )

    response = requests.get(url, timeout=settings.timeout)

    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, dict)

    assert "id" in data
    assert "n1" in data
    assert "years" in data

    assert str(data["id"]) == variable_id
    assert isinstance(data["n1"], str)
    assert data["n1"].strip() != ""
    assert isinstance(data["years"], list)
    assert all(isinstance(year, int) for year in data["years"])


def test_gus_bdl_variable_data(gus_response_schema):
    url = (
        f"{settings.gus_bdl_api_url}data/by-variable/"
        f"{VARIABLE_ID}?format=json&unit-id=0&page-size=10"
    )

    response = requests.get(url, timeout=settings.timeout)

    assert response.status_code == 200

    data = response.json()

    validate(
        instance=data,
        schema=gus_response_schema
    )


def test_gus_bdl_variable_data_contains_national_level():
    url = (
        f"{settings.gus_bdl_api_url}data/by-variable/"
        f"{VARIABLE_ID}?format=json&unit-id=0&year=2024&page-size=50"
    )

    response = requests.get(url, timeout=settings.timeout)

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, dict)
    assert "results" in data
    assert isinstance(data["results"], list)

    national_results = [
        result
        for result in data["results"]
        if result.get("id") == NATIONAL_LEVEL_ID
    ]

    assert national_results, (
        f"No data for country level: {NATIONAL_LEVEL_ID}"
    )

    assert isinstance(national_results[0]["values"], list)
    assert national_results[0]["values"]


def test_gus_bdl_variable_metadata_not_found():
    url = (
        f"{settings.gus_bdl_api_url}variables/"
        f"{VARIABLE_ID_FAKE}?format=json"
    )

    response = requests.get(url, timeout=settings.timeout)
    assert response.status_code == 404

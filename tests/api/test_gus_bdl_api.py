"""PolishMeter project tests for the real GUS BDL API.

Tests send actual HTTP requests to the GUS API and verify
response status codes, data structure, and content.
"""

import json
from pathlib import Path

import pytest
import requests
from jsonschema import validate

from config.settings import settings

CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / settings.gus_bdl_indicators_file
with CONFIG_PATH.open(encoding="utf-8") as file:
    config = json.load(file)
VARIABLE_IDS = list(config.keys())


@pytest.fixture(scope="session")
def gus_response_schema():
    """Load the JSON schema used to validate GUS BDL API responses."""
    schema_path = (
        Path(__file__).parent
        / "schemas"
        / "gus_bdl_data_schema.json"
    )

    with open(schema_path, encoding="utf-8") as file:
        return json.load(file)


@pytest.mark.parametrize("variable_id", VARIABLE_IDS)
def test_gus_bdl_variable_metadata(variable_id):
    """Verify that all configured variable IDs exist in the GUS BDL API."""
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


def test_gus_bdl_variable_data(gus_response_schema, test_resources):
    """Validate the GUS BDL variable data response against the JSON schema."""
    url = (
        f"{settings.gus_bdl_api_url}data/by-variable/"
        f"{test_resources["gus_test_data"]["variable_id"]}?format=json&unit-level=0"
    )

    response = requests.get(url, timeout=settings.timeout)

    assert response.status_code == 200

    data = response.json()

    validate(
        instance=data,
        schema=gus_response_schema
    )


def test_gus_bdl_variable_data_contains_national_level(test_resources):
    """Verify national-level data presence and ascending chronological order of years."""
    url = (
        f"{settings.gus_bdl_api_url}data/by-variable/"
        f"{test_resources["gus_test_data"]["variable_id"]}?format=json&unit-level=0"
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
        if result.get("id") == test_resources["gus_test_data"]["national_level_id"]
    ]

    assert national_results, (
        f"No data for country level: {test_resources["gus_test_data"]["national_level_id"]}"
    )

    values = national_results[0]["values"]
    assert isinstance(values, list)
    assert values

    # Ensure years are returned in ascending order (GusClient relies on values[-1])
    years = [int(item["year"]) for item in values]
    assert years == sorted(years), "Years from GUS API are not sorted ascending"


def test_gus_bdl_variable_metadata_not_found(test_resources):
    """Verify that the GUS BDL API returns 404 for a non-existent variable ID."""
    url = (
        f"{settings.gus_bdl_api_url}variables/"
        f"{test_resources["gus_test_data"]["variable_id_fake"]}?format=json"
    )

    response = requests.get(url, timeout=settings.timeout)
    assert response.status_code == 404

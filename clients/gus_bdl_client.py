"""Client for fetching and processing statistical indicators from the GUS BDL API.

This module provides the `GusClient` class, which downloads historical time-series
data from BDL, generates trend charts for configured indicators,
and transforms the latest values into standardized `Indicator` objects.
"""

import logging
from pathlib import Path
from utils.utils import (
    HttpClient,
    DateProvider,
    Indicator,
    ChartGenerator,
    ChartGenerationError,
    FileHandler,
)

log = logging.getLogger(__name__)


class GusException(Exception):
    """Base class for GUS-related exceptions."""

    def __init__(self, message, original_exception=None):
        super().__init__(message)
        self.original_exception = original_exception


class GusDataDownloadError(GusException):
    """Raised when data cannot be downloaded from GUS."""

    def __init__(self, data_name, original_exception=None):
        message = f"Nie udało się pobrać danych z GUS: {data_name}."
        super().__init__(message, original_exception)
        self.data_name = data_name


class GusClient:
    BASE_API_URL = "https://bdl.stat.gov.pl/api/v1/variables/"
    DATA_API_URL = "https://bdl.stat.gov.pl/api/v1/data/by-variable/"
    END_API_URL = "?format=json"
    SOURCE_API = "GUS BDL"
    NATIONAL_LEVEL_ID = "000000000000"

    def __init__(
        self,
        http_client: HttpClient,
        date_provider: DateProvider,
        indicators_config: dict,
        charts_dir: Path
    ):
        self.http_client = http_client
        self.date_provider = date_provider
        self.charts_dir = charts_dir

        # Build internal state per variable ID, extending config with data and chart placeholders
        self.data_dict = {
            variable_id: {
                **indicator_config,
                "years": [],
                "values": [],
                "generated_chart_path": None,
            }
            for variable_id, indicator_config in indicators_config.items()
        }

    def _get_download_date(self) -> str:
        """Return the current date and time of data download."""
        return self.date_provider.get_current_datetime().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    def _get_variable_metadata_url(self, variable_id: str) -> str:
        return f"{self.BASE_API_URL}{variable_id}{self.END_API_URL}"

    def _get_variable_metadata(self, url: str) -> dict:
        response = self._get_response(url)
        variable_metadata = response.json()
        return variable_metadata

    def _get_response(self, url: str):
        return self.http_client.request_with_retry(url)

    def _get_variable_data_url(self, variable_id: str) -> str:
        return (
            f"{self.DATA_API_URL}{variable_id}"
            f"{self.END_API_URL}"
            f"&unit-level=0"
        )


    def get_gus_bdl_data(self):
        """Download historical data for configured GUS indicators."""

        for variable_id, indicator_data in self.data_dict.items():

            try:
                data_url = self._get_variable_data_url(variable_id)
                response = self._get_response(data_url)
                data_json = response.json()

                x_chart_axis_values = []
                y_chart_axis_values = []

                for result in data_json.get("results", []):
                    if result.get("id") == self.NATIONAL_LEVEL_ID:
                        for value in result.get("values", []):
                            x_chart_axis_values.append(str(value["year"]))
                            y_chart_axis_values.append(value["val"])

                indicator_data["years"] = x_chart_axis_values
                indicator_data["values"] = y_chart_axis_values

            except Exception as exc:
                log.exception(
                    "Data not downloaded for variable %s",
                    indicator_data["name"],
                )
                raise GusDataDownloadError(
                    indicator_data["name"],
                    exc,
                ) from exc


    def create_chart_for_gus_bdl_data(self):
        """Generate charts for indicators configured to use charts."""
        chart_generator = ChartGenerator()

        for variable_id, indicator_data in self.data_dict.items():
            if not indicator_data.get("chart", False):
                continue

            try:
                chart_path = chart_generator.generate_chart(
                    data_dict=self.data_dict,
                    variable_id=variable_id,
                    output_dir=str(self.charts_dir),
                )
                indicator_data["generated_chart_path"] = chart_path
            except ChartGenerationError:
                log.exception(
                    "Chart not generated for indicator %s",
                    indicator_data["name"],
                )
                raise

    def generate_indicators_for_gus_bdl_data(self) -> list[Indicator]:
        """Generate Indicator objects for the latest available year and optional charts."""
        indicators = []
        download_date = self._get_download_date()

        for indicator_data in self.data_dict.values():
            years = indicator_data["years"]
            values = indicator_data["values"]

            if not years or not values:
                log.warning(
                    "No historical data for indicator %s",
                    indicator_data["name"],
                )
                continue

            # Select only the most recent available year (last item in the list)
            latest_year = years[-1]
            latest_value = values[-1]

            # Numeric indicator record for the latest year
            indicators.append(
                Indicator(
                    key=indicator_data["key"],
                    name=f"{indicator_data['name']} w {latest_year} roku",
                    value=latest_value,
                    unit=indicator_data["unit"],
                    source=self.SOURCE_API,
                    last_update_date=latest_year,
                    last_download_date=download_date,
                    group_name="GUS",
                    category=indicator_data["category"],
                    chart_path=None,
                )
            )

            # Separate chart record (if a chart was generated)
            chart_path = indicator_data.get("generated_chart_path")
            if chart_path:
                chart_key = indicator_data.get(
                    "key_chart", f"{indicator_data['key']}_chart"
                )
                indicators.append(
                    Indicator(
                        key=chart_key,
                        name=indicator_data.get("description", indicator_data["name"]),
                        value=None,
                        unit=None,
                        source=self.SOURCE_API,
                        last_update_date=latest_year,
                        last_download_date=download_date,
                        group_name="GUS",
                        category=indicator_data["category"],
                        chart_path=chart_path,
                    )
                )

        return indicators


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent

    charts_generated_path = project_root / "charts"
    charts_generated_path.mkdir(parents=True, exist_ok=True)

    gus_bdl_indicators_path = project_root / "config" / "gus_bdl_indicators.json"

    file_handler = FileHandler()
    indicators_config = file_handler.load_json(gus_bdl_indicators_path)

    http_client = HttpClient()
    date_provider = DateProvider()

    gus = GusClient(
        http_client=http_client,
        date_provider=date_provider,
        indicators_config=indicators_config,
        charts_dir=charts_generated_path
    )

    #url = gus._get_variable_data_url("459121", 2024)

    gus.get_gus_bdl_data()
    gus.create_chart_for_gus_bdl_data()

    indicators = gus.generate_indicators_for_gus_bdl_data()

    for indicator in indicators:
        print(indicator.to_dict())

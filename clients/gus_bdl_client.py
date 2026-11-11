
"""GUS client."""

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
import sys

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
    PAGE_SIZE = 50
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

        # Prepares the data structure for each GUS indicator,
        # preserving its configuration and creating space for the retrieved data.
        self.data_dict = {
            variable_id: {
                **indicator_config,
                "years": [],
                "values": [],
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

    def _get_variable_data_url(self, variable_id: str, year: int) -> str:
        return (
            f"{self.DATA_API_URL}{variable_id}"
            f"{self.END_API_URL}"
            f"&unit-id=0&year={year}"
            f"&page-size={self.PAGE_SIZE}"
        )

    def get_gus_bdl_data(self):
        """Download historical data for configured GUS indicators."""

        for variable_id, indicator_data in self.data_dict.items():

            try:
                url = self._get_variable_metadata_url(variable_id)
                variable_metadata = self._get_variable_metadata(url)

                # Place for future json validation

                available_years = variable_metadata["years"]
                x_chart_axis_values = []
                y_chart_axis_values = []

                for year in available_years:
                    data_url = self._get_variable_data_url(variable_id, year)

                    response = self._get_response(data_url)
                    year_data = response.json()

                    for result in year_data.get("results", []):
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
                chart_generator.generate_chart(
                    data_dict=self.data_dict,
                    variable_id=variable_id,
                    output_dir=self.charts_dir,
                )
            except ChartGenerationError:
                log.exception(
                    "Nie udało się wygenerować wykresu dla wskaźnika: %s",
                    indicator_data["name"],
                )
                raise

    def generate_indicators_for_gus_bdl_data(self) -> list[Indicator]:
        """Generate Indicator objects for the current and previous years."""

        indicators = []
        current_year = str(
            self.date_provider.get_current_date().year
        )
        download_date = self._get_download_date()

        for variable_id, indicator_data in self.data_dict.items():
            years = indicator_data["years"]
            values = indicator_data["values"]

            if not years or not values:
                log.warning(
                    "Brak danych historycznych dla wskaźnika %s",
                    indicator_data["name"],
                )
                continue

            if current_year in years:
                index = years.index(current_year)
                indexes = [index]

                if index > 0:
                    indexes.append(index - 1)
            else:
                indicators.append(
                    Indicator(
                        name=(
                            f"{indicator_data['name']} "
                            f"w {current_year} roku"
                        ),
                        value="Aktualnie brak danych od źródła",
                        unit=indicator_data["unit"],
                        source=self.SOURCE_API,
                        last_update_date="TO",
                        last_download_date=download_date,
                        group_name="GUS",
                        category=indicator_data["category"],
                    )
                )

                indexes = list(range(max(0, len(years) - 2), len(years)))
                indexes.reverse()

            for index in indexes:
                year = years[index]
                value = values[index]

                indicators.append(
                    Indicator(
                        name=f"{indicator_data['name']} w {year} roku",
                        value=value,
                        unit=indicator_data["unit"],
                        source=self.SOURCE_API,
                        last_update_date="TO",
                        last_download_date=download_date,
                        group_name="GUS",
                        category=indicator_data["category"],
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

    url = gus._get_variable_data_url("459121", 2024)

    gus.get_gus_bdl_data()
    gus.create_chart_for_gus_bdl_data()

    indicators = gus.generate_indicators_for_gus_bdl_data()

    for indicator in indicators:
        print(indicator.to_dict())

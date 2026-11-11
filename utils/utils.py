"Utils for all helpful functions."

import time
import os
import pytz
import requests
import ssl
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
import json
import logging
import matplotlib.pyplot as plt
from datetime import date, datetime
from pathlib import Path
from dataclasses import dataclass

logging.basicConfig(
    level=logging.INFO,  # lub DEBUG, jeśli chcesz więcej szczegółów
    format='%(levelname)s - %(message)s'
)

log = logging.getLogger(__name__)

class DateProvider:
    def __init__(self, tz_name: str = 'Europe/Warsaw'):
        self.tz = pytz.timezone(tz_name)

    def get_current_date(self) -> date:
        return datetime.now(self.tz).date() # datetime object includes year, month, day

    def get_current_datetime(self) -> datetime:
        return datetime.now(self.tz)

class CepikTLSAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False, **kwargs):
        context = ssl.create_default_context()
        context.set_ciphers("DEFAULT:@SECLEVEL=1")

        self.poolmanager = PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_context=context,
        )


class HttpClient():

    def __init__(
    self,
    max_retries: int = 10,
    timeout: int = 10,
    delay: int = 5,
    ):
        self.max_retries = max_retries
        self.timeout = timeout
        self.delay = delay

        self.session = requests.Session()
        
        # self.session.mount(
        #     "https://api.cepik.gov.pl/",
        #     CepikTLSAdapter()
        # )

    def request_with_retry(
            self,
            url: str,
            params: dict[str, str | int] | None = None,
        ) -> requests.Response:
            """Send HTTP request with timeout and retries, return response object.
    
            Method used for internal usage.
            """
    
            last_exception = None
            for attempt in range(1, self.max_retries + 1):
                try:
                    response = self.session.get(url, params=params, timeout=self.timeout)
                    response.raise_for_status()
                    return response
    
                except requests.exceptions.RequestException as e:
                    last_exception = e
                    log.warning("Error connection: %s (attempt %s/%s)", e, attempt, self.max_retries)
    
                if attempt < self.max_retries:
                    log.info("Next try in %s  sec...", self.delay)
                    time.sleep(self.delay)
    
            log.error("HTTP request failed after %s attempts: %s", self.max_retries, last_exception, exc_info=True) 
            if last_exception is None:
                raise RuntimeError("Request failed without an exception")
    
            raise last_exception


@dataclass
class Indicator:
    name: str
    value: int | float
    unit: str
    source: str
    last_update_date: str
    last_download_date: str
    group_name: str
    category: str
    chart_path: str
   

    def to_dict(self) -> dict[str, str | int | float]:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "source": self.source,
            "last_update_date": self.last_update_date,
            "last_download_date": self.last_download_date,
            "group_name": self.group_name,
            "category": self.category,
            "chart_path": self.chart_path
        }



class FileHandler:
    """Handle file operations."""

    def __init__(self, logger_name: str = "PolishMeter"):
        self.logger = logging.getLogger(logger_name)

    def load_json(self, path: str | Path) -> dict:
        """Load JSON data from a file."""
        path = Path(path)

        try:
            with path.open("r", encoding="utf-8") as file:
                return json.load(file)

        except (FileNotFoundError, PermissionError, json.JSONDecodeError):
            self.logger.exception("Failed to load JSON file: %s", path)
            raise


class ChartGenerationError(Exception):
    """Custom exception for chart generation errors."""
    pass


class ChartGenerator:
    def __init__(self):
        """
        Initializes the ChartGenerator.

        str = "." - means default value current directory, no need to have output_dir
        :param data_dict: Dictionary containing indicators data.
        :param variable_id: ID of the indicator to plot.
        :param output_dir: Directory where the chart will be saved.
        """


    def generate_chart(
        self,
        data_dict: dict,
        variable_id: str,
        output_dir: str = ".",
    ):
        """
        Draws a line chart for the selected indicator.
        Automatically adjusts figure size, label rotation, and tick density.
        Saves the chart to a file based on the 'description' field.
        Raises ChartGenerationError if data is invalid or saving fails.
        """
        if variable_id not in data_dict:
            raise ChartGenerationError(
                f"Indicator ID '{variable_id}' not found in data dictionary."
            )

        indicator = data_dict[variable_id]
        years = indicator.get("years", [])
        values = indicator.get("values", [])

        # Validate data
        if not years or not values:
            raise ChartGenerationError("No data available for plotting.")
        if len(years) != len(values):
            raise ChartGenerationError("Mismatch between number of years and values.")

        # ===============================
        # FIGURE SIZE CONFIGURATION
        # ===============================
        # Width grows with number of years, but is bounded
        min_width = 4.5           # minimum width in inches
        max_width = 7.0           # maximum width in inches
        width_per_year = 0.25     # inches per year

        fig_width = min(
            max(len(years) * width_per_year, min_width),
            max_width
        )

        fig_height = 3.0          # fixed height for layout consistency
        dpi = 100

        plt.figure(figsize=(fig_width, fig_height), dpi=dpi)

        # Plot
        plt.plot(years, values, marker="o", linewidth=1.5)
        plt.title(indicator.get("description", "Chart"))
        plt.xlabel(indicator.get("xlabel", "Year"))
        plt.ylabel(indicator.get("ylabel", "Value"))
        plt.xticks(rotation=45)

        # Reduce tick density if too many years
        if len(years) > 15:
            step = len(years) // 15
            plt.xticks(years[::step])

        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        # File path
        file_name = f"{indicator.get('save_as', 'chart')}.png"
        file_path = os.path.join(output_dir, file_name)

        try:
            plt.savefig(file_path, dpi=dpi)
        except Exception as e:
            plt.close()
            raise ChartGenerationError(
                f"Failed to save chart to '{file_path}': {e}"
            ) from e

        plt.close()
        return file_path

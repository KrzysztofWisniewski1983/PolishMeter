# PolishMeter

PolishMeter is a Python-based project focused on collecting, validating, processing and aggregating public data from various Polish sources, including CEPiK, GUS and NBP, etc.

The main focus of the project is data quality and test automation:

- Automated data collection from external sources.
- Data validation, verification and consistency checks.
- Data processing and aggregation.
- Automated testing using Pytest.
- Continuous test execution and reporting through CI/CD.

The web application provides a simple way to visualize the collected and processed data. Its purpose is to present the results of the data pipeline rather than to serve as a web development project. Web development and presentation-layer features are outside the main scope of this project.

This public repository contains selected directories and files related to data collection, processing, validation and test automation. The complete application is maintained separately in a private repository.

The primary focus is building a reliable data processing pipeline supported by testing and quality assurance.

## How to run

### Activate virtual environment (CMD)

.venv\Scripts\activate.bat

### Run web APP (CMD)
python -m uvicorn app:app --reload
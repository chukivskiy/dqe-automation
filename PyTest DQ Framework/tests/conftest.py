import pytest

from src.connectors.file_system.parquet_reader import ParquetReader
from src.connectors.postgres.postgres_connector import PostgresConnectorContextManager
from src.data_quality.data_quality_validation_library import DataQualityLibrary


def pytest_addoption(parser):
    parser.addoption("--db_host", action="store", default="localhost", help="Database host")
    parser.addoption("--db_name", action="store", default="mydatabase", help="Database name")
    parser.addoption("--db_port", type=int, default=5434, help="Database port")
    parser.addoption("--db_user", action="store", default=None, help="Database user")
    parser.addoption("--db_password", action="store", default=None, help="Database password")


def pytest_configure(config):
    informational_options = ("help", "version", "markers", "fixtures", "collectonly")
    if any(config.getoption(option, False) for option in informational_options):
        return

    required_options = ("--db_user", "--db_password")
    missing_options = [
        option
        for option in required_options
        if not config.getoption(option)
    ]
    if missing_options:
        raise pytest.UsageError(
            "Missing required database option(s): "
            + ", ".join(missing_options)
        )


@pytest.fixture(scope="session")
def db_connection(request):
    with PostgresConnectorContextManager(
        db_user=request.config.getoption("--db_user"),
        db_password=request.config.getoption("--db_password"),
        db_host=request.config.getoption("--db_host"),
        db_name=request.config.getoption("--db_name"),
        db_port=request.config.getoption("--db_port"),
    ) as db_connector:
        yield db_connector


@pytest.fixture(scope="session")
def parquet_reader():
    return ParquetReader()


@pytest.fixture(scope="session")
def data_quality_library():
    return DataQualityLibrary()

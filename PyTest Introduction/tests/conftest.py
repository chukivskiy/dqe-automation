import pytest
import pandas as pd

# Fixture to read the CSV file

@pytest.fixture(
    scope="session",
    params=["src/data/data.csv"]
)
def read_file(request):
    return pd.read_csv(request.param)

# Fixture to validate the schema of the file
@pytest.fixture(scope="session")
def validate_schema():
    def _validate_schema(actual_schema, expected_schema):
        assert actual_schema == expected_schema, (
            f"Expected schema: {expected_schema}\n"
            f"Actual schema: {actual_schema}"
        )

    return _validate_schema


# Pytest hook to mark unmarked tests with a custom mark
def pytest_collection_modifyitems(items):
    for item in items:
        if not list(item.iter_markers()):
            item.add_marker(pytest.mark.unmarked)
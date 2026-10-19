from unittest.mock import Mock

import pandas as pd
import pytest

from src.connectors.file_system.parquet_reader import ParquetReader
from src.connectors.postgres import postgres_connector
from src.connectors.postgres.postgres_connector import PostgresConnectorContextManager
from src.data_quality.data_quality_validation_library import DataQualityLibrary


def test_check_dataset_is_not_empty_accepts_rows():
    DataQualityLibrary.check_dataset_is_not_empty(pd.DataFrame({"value": [1]}))


def test_check_dataset_is_not_empty_reports_empty_dataset():
    with pytest.raises(AssertionError, match="Dataset is empty"):
        DataQualityLibrary.check_dataset_is_not_empty(pd.DataFrame(columns=["value"]))


def test_check_count_compares_row_counts():
    expected = pd.DataFrame({"value": [1, 2]})
    actual = pd.DataFrame({"value": [2, 1]})
    DataQualityLibrary.check_count(expected, actual)

    with pytest.raises(AssertionError, match="expected 2, actual 1"):
        DataQualityLibrary.check_count(expected, actual.iloc[:1])


def test_check_data_completeness_ignores_row_order():
    expected = pd.DataFrame({"name": ["Ada", "Grace"], "score": [1, 2]})
    actual = expected.iloc[::-1].reset_index(drop=True)
    DataQualityLibrary.check_data_completeness(expected, actual)


def test_check_data_completeness_ignores_column_order_and_equivalent_dtypes():
    expected = pd.DataFrame({"name": ["Ada"], "score": [1]})
    actual = pd.DataFrame({"score": [1.0], "name": ["Ada"]})

    DataQualityLibrary.check_data_completeness(expected, actual)


def test_check_data_completeness_reports_missing_and_extra_rows():
    expected = pd.DataFrame({"value": [1, 2]})
    actual = pd.DataFrame({"value": [1, 3]})

    with pytest.raises(AssertionError, match="Expected-only rows.*actual-only rows"):
        DataQualityLibrary.check_data_completeness(expected, actual)


def test_check_data_completeness_checks_duplicate_row_multiplicity():
    expected = pd.DataFrame({"value": [1, 1]})
    actual = pd.DataFrame({"value": [1, 2]})

    with pytest.raises(AssertionError, match="Expected-only rows"):
        DataQualityLibrary.check_data_completeness(expected, actual)


def test_check_data_completeness_reports_column_mismatch():
    expected = pd.DataFrame({"expected": [1]})
    actual = pd.DataFrame({"actual": [1]})

    with pytest.raises(AssertionError, match="Column mismatch"):
        DataQualityLibrary.check_data_completeness(expected, actual)


def test_check_duplicates_checks_full_rows():
    rows = pd.DataFrame({"key": [1, 2], "value": ["a", "a"]})
    DataQualityLibrary.check_duplicates(rows)

    with pytest.raises(AssertionError, match="duplicate row"):
        DataQualityLibrary.check_duplicates(
            pd.DataFrame({"key": [1, 1], "value": ["a", "a"]})
        )


def test_check_duplicates_can_check_selected_columns():
    rows = pd.DataFrame({"key": [1, 1], "value": ["a", "b"]})

    with pytest.raises(AssertionError, match="using columns \\['key'\\]"):
        DataQualityLibrary.check_duplicates(rows, column_names=["key"])


def test_check_not_null_values_reports_null_column_counts():
    data = pd.DataFrame({"name": ["Ada", None], "score": [1, None]})

    with pytest.raises(AssertionError, match="name.*score"):
        DataQualityLibrary.check_not_null_values(data, ["name", "score"])


def test_check_not_null_values_rejects_unknown_columns():
    with pytest.raises(ValueError, match="not found"):
        DataQualityLibrary.check_not_null_values(pd.DataFrame({"name": ["Ada"]}), ["age"])


def test_postgres_connector_opens_queries_and_closes_connection(monkeypatch):
    connection = Mock()
    connection.closed = 0
    connect = Mock(return_value=connection)
    read_sql_query = Mock(return_value=pd.DataFrame({"value": [1]}))
    monkeypatch.setattr(postgres_connector.psycopg2, "connect", connect)
    monkeypatch.setattr(postgres_connector.pd, "read_sql_query", read_sql_query)

    connector = PostgresConnectorContextManager(
        db_user="user",
        db_password="password",
        db_host="db-host",
        db_name="database",
        db_port=5432,
    )
    with connector as active_connector:
        result = active_connector.get_data_sql("SELECT 1 AS value")

    connect.assert_called_once_with(
        host="db-host",
        port=5432,
        database="database",
        user="user",
        password="password",
    )
    assert connection.autocommit is False
    read_sql_query.assert_called_once_with("SELECT 1 AS value", connection)
    pd.testing.assert_frame_equal(result, pd.DataFrame({"value": [1]}))
    connection.close.assert_called_once_with()
    assert connector.get_connection() is None


def test_postgres_connector_rejects_query_without_active_connection():
    connector = PostgresConnectorContextManager(db_user="user", db_password="password")
    with pytest.raises(RuntimeError, match="No active PostgreSQL connection"):
        connector.get_data_sql("SELECT 1")


def test_parquet_reader_reads_direct_and_nested_files(tmp_path):
    root_file = tmp_path / "root.parquet"
    nested_file = tmp_path / "partition" / "nested.parquet"
    nested_file.parent.mkdir()
    pd.DataFrame({"value": [1]}).to_parquet(root_file, index=False)
    pd.DataFrame({"value": [2]}).to_parquet(nested_file, index=False)
    reader = ParquetReader()

    direct_rows = reader.process(str(tmp_path))
    all_rows = reader.process(str(tmp_path), include_subfolders=True)

    assert direct_rows["value"].tolist() == [1]
    assert sorted(all_rows["value"].tolist()) == [1, 2]


def test_parquet_reader_reads_partitioned_dataset_and_reports_missing_path(tmp_path):
    partition_file = tmp_path / "visit_date=2025-01-01" / "part-0.parquet"
    partition_file.parent.mkdir()
    pd.DataFrame({"value": [10]}).to_parquet(partition_file, index=False)

    data = ParquetReader().process(str(tmp_path), include_subfolders=True)

    assert data["value"].tolist() == [10]
    assert data["visit_date"].astype(str).tolist() == ["2025-01-01"]

    with pytest.raises(FileNotFoundError, match="does not exist"):
        ParquetReader().process(str(tmp_path / "absent"))

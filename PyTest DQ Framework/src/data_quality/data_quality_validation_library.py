from collections import Counter
from typing import Iterable, Optional, Sequence

import numpy as np
import pandas as pd
from pandas import DataFrame


class DataQualityLibrary:
    """Reusable data-quality assertions for pandas DataFrames."""

    @staticmethod
    def _require_dataframe(df: DataFrame, argument_name: str) -> None:
        if not isinstance(df, pd.DataFrame):
            raise TypeError(
                f"{argument_name} must be a pandas DataFrame; "
                f"got {type(df).__name__}."
            )

    @staticmethod
    def _validated_columns(df: DataFrame, column_names: Sequence[str]) -> list:
        if (
            column_names is None
            or isinstance(column_names, str)
            or len(column_names) == 0
        ):
            raise ValueError("column_names must be a non-empty sequence of column names.")

        missing_columns = [name for name in column_names if name not in df.columns]
        if missing_columns:
            raise ValueError(f"Columns not found in DataFrame: {missing_columns}")
        return list(column_names)

    @staticmethod
    def _canonical_value(value):
        if isinstance(value, (list, tuple)):
            return tuple(DataQualityLibrary._canonical_value(item) for item in value)
        if isinstance(value, dict):
            items = (
                (
                    DataQualityLibrary._canonical_value(key),
                    DataQualityLibrary._canonical_value(item),
                )
                for key, item in value.items()
            )
            return tuple(sorted(items, key=repr))
        if isinstance(value, set):
            return tuple(sorted(
                (DataQualityLibrary._canonical_value(item) for item in value),
                key=repr,
            ))

        if isinstance(value, np.generic):
            value = value.item()

        is_null = pd.isna(value)
        if isinstance(is_null, (bool, np.bool_)) and is_null:
            return DataQualityLibrary._NULL_VALUE
        return value

    _NULL_VALUE = object()

    @staticmethod
    def _row_keys(df: DataFrame) -> list:
        return [
            tuple(DataQualityLibrary._canonical_value(value) for value in row)
            for row in df.itertuples(index=False, name=None)
        ]

    @staticmethod
    def _unmatched_records(
        df: DataFrame, row_keys: Iterable[tuple], other_row_keys: Iterable[tuple]
    ) -> list:
        available = Counter(other_row_keys)
        unmatched = []
        for position, row_key in enumerate(row_keys):
            if available[row_key]:
                available[row_key] -= 1
            else:
                unmatched.append(df.iloc[position].to_dict())
        return unmatched[:5]

    @staticmethod
    def check_dataset_is_not_empty(df: DataFrame) -> None:
        DataQualityLibrary._require_dataframe(df, "df")
        assert not df.empty, "Dataset is empty; expected at least one row."

    @staticmethod
    def check_count(df_expected: DataFrame, df_actual: DataFrame) -> None:
        DataQualityLibrary._require_dataframe(df_expected, "df_expected")
        DataQualityLibrary._require_dataframe(df_actual, "df_actual")
        expected_count = len(df_expected)
        actual_count = len(df_actual)
        assert expected_count == actual_count, (
            f"Row count mismatch: expected {expected_count}, actual {actual_count}."
        )

    @staticmethod
    def check_data_completeness(df_expected: DataFrame, df_actual: DataFrame) -> None:
        DataQualityLibrary._require_dataframe(df_expected, "df_expected")
        DataQualityLibrary._require_dataframe(df_actual, "df_actual")

        expected_columns = list(df_expected.columns)
        actual_columns = list(df_actual.columns)
        assert len(expected_columns) == len(set(expected_columns)), (
            "Expected DataFrame contains duplicate column names."
        )
        assert len(actual_columns) == len(set(actual_columns)), (
            "Actual DataFrame contains duplicate column names."
        )
        missing_columns = [name for name in expected_columns if name not in actual_columns]
        unexpected_columns = [name for name in actual_columns if name not in expected_columns]
        assert not missing_columns and not unexpected_columns, (
            "Column mismatch: "
            f"missing from actual={missing_columns}, "
            f"unexpected in actual={unexpected_columns}."
        )

        expected = df_expected.loc[:, expected_columns].reset_index(drop=True)
        actual = df_actual.loc[:, expected_columns].reset_index(drop=True)
        expected_rows = DataQualityLibrary._row_keys(expected)
        actual_rows = DataQualityLibrary._row_keys(actual)

        if Counter(expected_rows) != Counter(actual_rows):
            expected_only = DataQualityLibrary._unmatched_records(
                expected, expected_rows, actual_rows
            )
            actual_only = DataQualityLibrary._unmatched_records(
                actual, actual_rows, expected_rows
            )
            raise AssertionError(
                "Data completeness mismatch (row order ignored). "
                f"Expected-only rows (up to 5): {expected_only}; "
                f"actual-only rows (up to 5): {actual_only}."
            )

    @staticmethod
    def check_duplicates(
        df: DataFrame, column_names: Optional[Sequence[str]] = None
    ) -> None:
        DataQualityLibrary._require_dataframe(df, "df")
        subset = (
            DataQualityLibrary._validated_columns(df, column_names)
            if column_names is not None
            else None
        )
        duplicate_mask = df.duplicated(subset=subset, keep=False)
        duplicate_rows = df.loc[duplicate_mask]
        assert duplicate_rows.empty, (
            f"Found {len(duplicate_rows)} duplicate row(s) "
            f"using columns {subset or list(df.columns)}. "
            f"Examples (up to 5): {duplicate_rows.head(5).to_dict(orient='records')}."
        )

    @staticmethod
    def check_not_null_values(df: DataFrame, column_names: Sequence[str]) -> None:
        DataQualityLibrary._require_dataframe(df, "df")
        columns = DataQualityLibrary._validated_columns(df, column_names)
        null_counts = df[columns].isna().sum()
        columns_with_nulls = null_counts[null_counts > 0]
        assert columns_with_nulls.empty, (
            "Null values found in columns: "
            f"{columns_with_nulls.to_dict()}."
        )

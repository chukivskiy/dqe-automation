from pathlib import Path

import pandas as pd
from pandas import DataFrame


class ParquetReader:
    """Read Parquet files or partitioned Parquet dataset directories."""

    def process(
        self, target_path: str, include_subfolders: bool = False
    ) -> DataFrame:
        path = Path(target_path)
        if not path.exists():
            raise FileNotFoundError(f"Parquet path does not exist: {path}")
        if path.is_file():
            return pd.read_parquet(path, engine="pyarrow")
        if not path.is_dir():
            raise ValueError(f"Parquet path is not a file or directory: {path}")

        if include_subfolders:
            if not any(path.rglob("*.parquet")):
                raise FileNotFoundError(f"No Parquet files found in directory: {path}")
            return pd.read_parquet(path, engine="pyarrow")

        parquet_files = sorted(path.glob("*.parquet"))
        if not parquet_files:
            raise FileNotFoundError(
                f"No Parquet files found directly in directory: {path}"
            )

        frames = [
            pd.read_parquet(parquet_file, engine="pyarrow")
            for parquet_file in parquet_files
        ]
        return pd.concat(frames, ignore_index=True)

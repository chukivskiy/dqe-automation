from typing import Optional

import pandas as pd
import psycopg2
from pandas import DataFrame
from psycopg2.extensions import connection


class PostgresConnectorContextManager:
    """Manage a PostgreSQL connection and return query results as DataFrames."""

    def __init__(
        self,
        db_user: str,
        db_password: str,
        db_host: str = "localhost",
        db_name: str = "mydatabase",
        db_port: int = 5434,
        autocommit: bool = False,
    ) -> None:
        self.db_user = db_user
        self.db_password = db_password
        self.db_host = db_host
        self.db_name = db_name
        self.db_port = db_port
        self.autocommit = autocommit
        self.connection: Optional[connection] = None

    def __enter__(self) -> "PostgresConnectorContextManager":
        self.connection = psycopg2.connect(
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
            user=self.db_user,
            password=self.db_password,
        )
        self.connection.autocommit = self.autocommit
        return self

    def __exit__(self, exc_type, exc_value, exc_tb) -> None:
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def get_connection(self) -> Optional[connection]:
        return self.connection

    def get_data_sql(self, query: str) -> DataFrame:
        if self.connection is None or self.connection.closed:
            raise RuntimeError(
                "No active PostgreSQL connection. Use the connector as a context manager."
            )
        return pd.read_sql_query(query, self.connection)

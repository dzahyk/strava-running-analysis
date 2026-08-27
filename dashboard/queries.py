"""
Query layer for the Strava Running Analysis V2 dashboard.

This module initializes DuckDB from the project's SQL scripts and
provides small reusable functions that return Pandas DataFrames.

V2 source of truth:
    data/processed/activities_run_clean.csv

The raw Strava export is never read by this module.
"""

from pathlib import Path

import duckdb
import pandas as pd


# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = PROJECT_ROOT / "sql"

SQL_FILES = [
    SQL_DIR / "01_create_table.sql",
    SQL_DIR / "02_kpi_queries.sql",
    SQL_DIR / "03_dashboard_views.sql",
]


def initialize_database(database: str = ":memory:") -> duckdb.DuckDBPyConnection:
    """
    Initialize a DuckDB database and execute all V2 SQL scripts.

    By default, an in-memory database is used. This means the dashboard
    does not depend on the local strava_running.duckdb file.

    Parameters
    ----------
    database:
        DuckDB database path. Defaults to ":memory:".

    Returns
    -------
    duckdb.DuckDBPyConnection
        Ready-to-query DuckDB connection.
    """
    connection = duckdb.connect(database)

    for sql_file in SQL_FILES:
        sql = sql_file.read_text(encoding="utf-8")
        connection.execute(sql)

    return connection


def get_kpi_summary(
    connection: duckdb.DuckDBPyConnection,
) -> pd.DataFrame:
    """Return the overall KPI summary."""
    return connection.execute(
        """
        SELECT *
        FROM v_kpi_summary
        """
    ).df()


def get_monthly_summary(
    connection: duckdb.DuckDBPyConnection,
) -> pd.DataFrame:
    """Return monthly running metrics in chronological order."""
    return connection.execute(
        """
        SELECT *
        FROM v_monthly_summary
        ORDER BY month_start
        """
    ).df()


def get_weekday_summary(
    connection: duckdb.DuckDBPyConnection,
) -> pd.DataFrame:
    """Return running metrics ordered Monday through Sunday."""
    return connection.execute(
        """
        SELECT *
        FROM v_weekday_summary
        ORDER BY weekday_number
        """
    ).df()


def get_distance_categories(
    connection: duckdb.DuckDBPyConnection,
) -> pd.DataFrame:
    """Return running metrics grouped by distance category."""
    return connection.execute(
        """
        SELECT *
        FROM v_distance_category
        ORDER BY category_order
        """
    ).df()


def get_longest_runs(
    connection: duckdb.DuckDBPyConnection,
    limit: int = 10,
) -> pd.DataFrame:
    """
    Return the longest runs ordered by distance rank.

    Parameters
    ----------
    connection:
        Active DuckDB connection.
    limit:
        Number of ranked runs to return. Defaults to 10.
    """
    if limit < 1:
        raise ValueError("limit must be at least 1")

    return connection.execute(
        """
        SELECT *
        FROM v_longest_runs
        WHERE distance_rank <= ?
        ORDER BY distance_rank
        """,
        [limit],
    ).df()

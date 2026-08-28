"""
Query layer for the Strava Running Analysis V2 dashboard.

This module initializes DuckDB from the project's SQL scripts and
provides reusable functions for dashboard data access.

V2 source of truth:
    data/processed/activities_run_clean.csv

The raw Strava export is never read by this module.

Interactive filtering:
    year_month=None
        -> use the full analytical dataset

    year_month="YYYY-MM"
        -> calculate filtered metrics from v_run_details
"""

from pathlib import Path

import duckdb
import pandas as pd


# ------------------------------------------------------------
# Project paths
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = PROJECT_ROOT / "sql"

DISTANCE_CATEGORY_LABELS = {
    "Short": "Short (<5 km)",
    "Medium": "Medium (5-<10 km)",
    "Long": "Long (10-<15 km)",
    "Very Long": "Very Long (>=15 km)",
}


def _distance_category_label(
    distance_category: str,
) -> str:
    """Map canonical dashboard category to SQL label."""
    try:
        return DISTANCE_CATEGORY_LABELS[distance_category]
    except KeyError as exc:
        raise ValueError(
            f"Unsupported distance category: {distance_category}"
        ) from exc


SQL_FILES = [
    SQL_DIR / "01_create_table.sql",
    SQL_DIR / "02_kpi_queries.sql",
    SQL_DIR / "03_dashboard_views.sql",
]


# ------------------------------------------------------------
# Database initialization
# ------------------------------------------------------------

def initialize_database(
    database: str = ":memory:",
) -> duckdb.DuckDBPyConnection:
    """
    Initialize DuckDB and execute all V2 SQL scripts.

    By default, an in-memory database is used so the dashboard
    does not depend on the local strava_running.duckdb file.
    """
    connection = duckdb.connect(database)

    for sql_file in SQL_FILES:
        sql = sql_file.read_text(encoding="utf-8")
        connection.execute(sql)

    return connection


# ------------------------------------------------------------
# Filter options
# ------------------------------------------------------------

def get_available_months(
    connection: duckdb.DuckDBPyConnection,
) -> list[str]:
    """Return available analysis months in chronological order."""
    result = connection.execute(
        """
        SELECT DISTINCT
            year_month
        FROM v_run_details
        ORDER BY
            year_month
        """
    ).df()

    return result["year_month"].tolist()


# ------------------------------------------------------------
# KPI summary
# ------------------------------------------------------------

def get_kpi_summary(
    connection: duckdb.DuckDBPyConnection,
    year_month: str | None = None,
    distance_category: str | None = None,
) -> pd.DataFrame:
    """
    Return KPI metrics for the active dashboard context.

    With no filters, preserve the existing overall KPI view.
    When month and/or distance category filters are active,
    recalculate metrics from v_run_details.
    """
    if year_month is None and distance_category is None:
        return connection.execute(
            """
            SELECT *
            FROM v_kpi_summary
            """
        ).df()

    filters = []
    parameters = []

    if year_month is not None:
        filters.append("year_month = ?")
        parameters.append(year_month)

    if distance_category is not None:
        filters.append("distance_category = ?")
        parameters.append(_distance_category_label(distance_category))

    where_clause = " AND ".join(filters)

    return connection.execute(
        f"""
        SELECT
            COUNT(*) AS total_runs,
            ROUND(
                SUM(distance_km),
                2
            ) AS total_distance_km,
            ROUND(
                AVG(distance_km),
                2
            ) AS average_distance_km,
            ROUND(
                MAX(distance_km),
                2
            ) AS longest_run_km,
            ROUND(
                SUM(moving_time_sec) / 3600.0,
                2
            ) AS total_moving_hours,
            ROUND(
                (SUM(moving_time_sec) / 60.0)
                / NULLIF(SUM(distance_km), 0),
                4
            ) AS weighted_pace_min_km,
            MIN(activity_date) AS start_date,
            MAX(activity_date) AS end_date
        FROM v_run_details
        WHERE {where_clause}
        """,
        parameters,
    ).df()



# ------------------------------------------------------------
# Monthly trend
# ------------------------------------------------------------

def get_monthly_summary(
    connection: duckdb.DuckDBPyConnection,
) -> pd.DataFrame:
    """
    Return the full monthly running trend.

    This remains unfiltered so the dashboard preserves temporal
    context even when a single month is selected.
    """
    return connection.execute(
        """
        SELECT *
        FROM v_monthly_summary
        ORDER BY month_start
        """
    ).df()


# ------------------------------------------------------------
# Weekday summary
# ------------------------------------------------------------

def get_weekday_summary(
    connection: duckdb.DuckDBPyConnection,
    year_month: str | None = None,
    distance_category: str | None = None,
) -> pd.DataFrame:
    """Return weekday metrics for the active dashboard context."""
    if year_month is None and distance_category is None:
        return connection.execute(
            """
            SELECT *
            FROM v_weekday_summary
            ORDER BY weekday_number
            """
        ).df()

    filters = []
    parameters = []

    if year_month is not None:
        filters.append("year_month = ?")
        parameters.append(year_month)

    if distance_category is not None:
        filters.append("distance_category = ?")
        parameters.append(_distance_category_label(distance_category))

    where_clause = " AND ".join(filters)

    return connection.execute(
        f"""
        SELECT
            weekday_number,
            day_name,
            COUNT(*) AS total_runs,
            ROUND(
                SUM(distance_km),
                2
            ) AS total_distance_km,
            ROUND(
                (SUM(moving_time_sec) / 60.0)
                / NULLIF(SUM(distance_km), 0),
                4
            ) AS weighted_pace_min_km
        FROM v_run_details
        WHERE {where_clause}
        GROUP BY
            weekday_number,
            day_name
        ORDER BY
            weekday_number
        """,
        parameters,
    ).df()



# ------------------------------------------------------------
# Distance category summary
# ------------------------------------------------------------

def get_distance_categories(
    connection: duckdb.DuckDBPyConnection,
    year_month: str | None = None,
) -> pd.DataFrame:
    """Return overall or month-filtered distance categories."""
    if year_month is None:
        return connection.execute(
            """
            SELECT *
            FROM v_distance_category
            ORDER BY category_order
            """
        ).df()

    return connection.execute(
        """
        SELECT
            category_order,
            distance_category,

            COUNT(*) AS total_runs,

            ROUND(
                SUM(distance_km),
                2
            ) AS total_distance_km,

            ROUND(
                AVG(distance_km),
                2
            ) AS average_distance_km,

            ROUND(
                (SUM(moving_time_sec) / 60.0)
                / NULLIF(SUM(distance_km), 0),
                4
            ) AS weighted_pace_min_km

        FROM v_run_details

        WHERE year_month = ?

        GROUP BY
            category_order,
            distance_category

        ORDER BY
            category_order
        """,
        [year_month],
    ).df()


# ------------------------------------------------------------
# Ranked longest runs
# ------------------------------------------------------------

def get_longest_runs(
    connection: duckdb.DuckDBPyConnection,
    limit: int = 10,
    year_month: str | None = None,
    distance_category: str | None = None,
) -> pd.DataFrame:
    """
    Return ranked longest runs for the active dashboard context.

    Ranking is recalculated after month/category filtering so
    ROW_NUMBER() always restarts at 1 for the active subset.
    """
    if limit < 1:
        raise ValueError("limit must be at least 1")

    if year_month is None and distance_category is None:
        return connection.execute(
            """
            SELECT *
            FROM v_longest_runs
            WHERE distance_rank <= ?
            ORDER BY distance_rank
            """,
            [limit],
        ).df()

    filters = []
    parameters = []

    if year_month is not None:
        filters.append("year_month = ?")
        parameters.append(year_month)

    if distance_category is not None:
        filters.append("distance_category = ?")
        parameters.append(_distance_category_label(distance_category))

    where_clause = " AND ".join(filters)

    parameters.append(limit)

    return connection.execute(
        f"""
        WITH filtered_runs AS (
            SELECT *
            FROM v_run_details
            WHERE {where_clause}
        ),
        ranked_runs AS (
            SELECT
                ROW_NUMBER() OVER (
                    ORDER BY
                        distance_km DESC,
                        activity_date ASC,
                        activity_id ASC
                ) AS distance_rank,
                activity_id,
                activity_date,
                distance_km,
                moving_time_min,
                pace_min_km,
                speed_kmh,
                elevation_gain_m,
                year_month,
                day_name
            FROM filtered_runs
        )
        SELECT *
        FROM ranked_runs
        WHERE distance_rank <= ?
        ORDER BY distance_rank
        """,
        parameters,
    ).df()

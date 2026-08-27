-- ============================================================
-- Strava Running Analysis
-- V2 - Dashboard Views
-- File: 03_dashboard_views.sql
--
-- Purpose:
-- Create reusable analytical views for the Streamlit dashboard.
--
-- Source table:
-- activities_run
--
-- Metric contract:
-- - distance_km is the canonical distance metric.
-- - aggregated pace uses total moving time / total distance.
-- ============================================================


-- ============================================================
-- 1. Monthly Running Summary
-- ============================================================

CREATE OR REPLACE VIEW v_monthly_summary AS

WITH monthly_aggregation AS (
    SELECT
        CAST(DATE_TRUNC('month', activity_date) AS DATE) AS month_start,
        COUNT(*) AS total_runs,
        SUM(distance_km) AS total_distance_km,
        AVG(distance_km) AS average_distance_km,
        MAX(distance_km) AS longest_run_km,
        SUM(moving_time_sec) AS total_moving_time_sec
    FROM activities_run
    GROUP BY
        DATE_TRUNC('month', activity_date)
)

SELECT
    month_start,

    STRFTIME(month_start, '%Y-%m') AS year_month,

    total_runs,

    ROUND(
        total_distance_km,
        2
    ) AS total_distance_km,

    ROUND(
        average_distance_km,
        2
    ) AS average_distance_km,

    ROUND(
        longest_run_km,
        2
    ) AS longest_run_km,

    ROUND(
        total_moving_time_sec / 3600.0,
        2
    ) AS total_moving_hours,

    ROUND(
        (total_moving_time_sec / 60.0)
        / NULLIF(total_distance_km, 0),
        4
    ) AS weighted_pace_min_km

FROM monthly_aggregation;


-- ============================================================
-- 2. Running Summary by Day of Week
-- ============================================================

CREATE OR REPLACE VIEW v_weekday_summary AS

WITH weekday_aggregation AS (
    SELECT
        CAST(EXTRACT(ISODOW FROM activity_date) AS INTEGER) AS weekday_number,
        day_name,
        COUNT(*) AS total_runs,
        SUM(distance_km) AS total_distance_km,
        SUM(moving_time_sec) AS total_moving_time_sec
    FROM activities_run
    GROUP BY
        EXTRACT(ISODOW FROM activity_date),
        day_name
)

SELECT
    weekday_number,
    day_name,
    total_runs,

    ROUND(
        total_distance_km,
        2
    ) AS total_distance_km,

    ROUND(
        (total_moving_time_sec / 60.0)
        / NULLIF(total_distance_km, 0),
        4
    ) AS weighted_pace_min_km

FROM weekday_aggregation;


-- ============================================================
-- 3. Running Summary by Distance Category
-- ============================================================

CREATE OR REPLACE VIEW v_distance_category AS

WITH categorized_runs AS (
    SELECT
        activity_id,
        distance_km,
        moving_time_sec,

        CASE
            WHEN distance_km < 5 THEN 1
            WHEN distance_km < 10 THEN 2
            WHEN distance_km < 15 THEN 3
            ELSE 4
        END AS category_order,

        CASE
            WHEN distance_km < 5 THEN 'Short (<5 km)'
            WHEN distance_km < 10 THEN 'Medium (5-<10 km)'
            WHEN distance_km < 15 THEN 'Long (10-<15 km)'
            ELSE 'Very Long (>=15 km)'
        END AS distance_category

    FROM activities_run
)

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

FROM categorized_runs

GROUP BY
    category_order,
    distance_category;


-- ============================================================
-- 4. Running Distance Ranking
-- ============================================================

CREATE OR REPLACE VIEW v_longest_runs AS

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

FROM activities_run;

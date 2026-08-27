-- ============================================================
-- Strava Running Analysis
-- V2 - KPI Queries
-- File: 02_kpi_queries.sql
--
-- Purpose:
-- Create the core KPI summary used for V1-to-V2 reconciliation
-- and later consumed by the Streamlit dashboard.
--
-- Metric contract inherited from V1:
-- - distance_km is the canonical distance metric.
-- - weighted pace = total moving time / total distance.
-- ============================================================

CREATE OR REPLACE VIEW v_kpi_summary AS

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

FROM activities_run;

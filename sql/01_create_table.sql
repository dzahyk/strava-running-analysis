-- ============================================================
-- Strava Running Analysis
-- V2 - SQL Foundation
-- File: 01_create_table.sql
--
-- Purpose:
-- Create the base analytical table used by V2.
--
-- Source:
-- data/processed/activities_run_clean.csv
--
-- Important:
-- - Source data has already been cleaned and sanitized in V1.
-- - activity_id is a surrogate ID, not the original Strava ID.
-- - V2 does not read the raw Strava ZIP.
-- ============================================================

DROP TABLE IF EXISTS activities_run;

CREATE TABLE activities_run (
    activity_id INTEGER PRIMARY KEY,
    activity_date DATE NOT NULL,
    distance_km DOUBLE NOT NULL,
    moving_time_sec INTEGER NOT NULL,
    moving_time_min DOUBLE NOT NULL,
    pace_min_km DOUBLE NOT NULL,
    speed_kmh DOUBLE NOT NULL,
    elevation_gain_m DOUBLE,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    year_month VARCHAR NOT NULL,
    day_name VARCHAR NOT NULL
);

INSERT INTO activities_run
SELECT
    CAST(activity_id AS INTEGER),
    CAST(activity_date AS DATE),
    CAST(distance_km AS DOUBLE),
    CAST(moving_time_sec AS INTEGER),
    CAST(moving_time_min AS DOUBLE),
    CAST(pace_min_km AS DOUBLE),
    CAST(speed_kmh AS DOUBLE),
    CAST(elevation_gain_m AS DOUBLE),
    CAST(year AS INTEGER),
    CAST(month AS INTEGER),
    CAST(year_month AS VARCHAR),
    CAST(day_name AS VARCHAR)
FROM read_csv_auto(
    'data/processed/activities_run_clean.csv',
    header = true
);

# Strava Running Analysis

A progressive data analytics portfolio project built from a sanitized personal Strava activity export.

## Current Release

**V1 — Personal Running Activity Analysis**

V1 focuses on data cleaning, exploratory data analysis, metric definition, visualization, and privacy-aware preparation of a reusable analytical dataset.

## Dataset

- Raw activities: 185
- Running activities: 126
- Raw export period: 9 Nov 2025 - 22 Jul 2026
- Run analysis period: 12 Nov 2025 - 22 Jul 2026
- Total running distance: 1,065.91 km
- Average distance per run: 8.46 km
- Longest run: 23.60 km
- Overall weighted pace: approximately 7:09 /km

The public analytical dataset contains sanitized running activity data only.

Raw Strava exports, original activity identifiers, filenames, precise GPS data, profile information, login information, and device identifiers are not published.

## V1 Metric Definitions

### Distance

Canonical running distance:

`distance_km = Distance.1 / 1000`

`Distance.1` contains the more precise meter-level distance from the Strava export.

### Weighted Pace

Overall and aggregated pace are calculated using:

`total moving time / total distance`

This avoids the bias that would result from taking a simple mean of activity-level pace.

## V1 Analysis

The notebook includes:

- Overall running KPI summary
- Monthly running distance
- Monthly running frequency
- Monthly weighted pace
- Running distance distribution
- Running frequency by weekday
- Distance vs running pace
- Top 10 longest runs
- Cumulative running distance

## V1 Outputs

### Notebook

`notebooks/v1_running_analysis.ipynb`

### Processed Data

- `data/processed/activities_run_clean.csv`
- `data/processed/monthly_running_summary.csv`
- `data/processed/v1_summary_metrics.csv`
- `data/processed/v1_data_quality_report.csv`

### Charts

Charts are stored in:

`images/charts/`

## Key V1 Findings

- January 2026 recorded the highest monthly running distance at approximately 209 km.
- January 2026 also recorded the highest monthly run frequency with 22 runs.
- The fastest monthly weighted pace in the observed data occurred in November 2025 at approximately 6:46 /km.
- Saturday was the most frequent running day, with 25 recorded runs.
- The longest recorded run was approximately 23.60 km.

The first and last months in the dataset are partial observation periods, so monthly comparisons should be interpreted with that limitation in mind.

## Privacy

The raw Strava export is intentionally excluded from the public repository.

Only sanitized analytical datasets are intended for publication.

## Project Progression

- V1: Python / Pandas exploratory analysis
- V2: DuckDB SQL + Streamlit + Plotly interactive dashboard
- V3+: Progressive analytical extensions

## Next Step

V2 will use `activities_run_clean.csv` as its analytical input, query and aggregate the data using DuckDB SQL, reconcile core KPIs against V1, and present the results in an interactive Streamlit dashboard.

# Strava Running Analysis

A progressive data analytics portfolio project built from a sanitized personal Strava activity export.

The project evolves from exploratory analysis in Python and Pandas into a reproducible SQL analytics layer and an interactive Streamlit dashboard powered by DuckDB and Plotly.

## Current Release

**V2 — DuckDB SQL + Interactive Streamlit Dashboard**

V2 extends the validated V1 analytical dataset into a reusable SQL and dashboard workflow.

The current release includes:

- DuckDB-based analytical SQL
- Reconciled running KPIs
- Monthly running trends
- Weekday running patterns
- Distance-category analysis
- SQL window-function ranking for longest runs
- Interactive month filtering
- Streamlit dashboard presentation
- Plotly visualizations
- In-memory database initialization for reproducibility
- Privacy-aware use of sanitized data only

V1 remains the baseline exploratory analysis and metric-definition layer.

## Key Metrics

The validated running dataset contains:

- Running activities: 126
- Run analysis period: 12 Nov 2025 - 22 Jul 2026
- Total running distance: 1,065.91 km
- Average distance per run: 8.46 km
- Longest run: 23.60 km
- Total moving time: 126.92 hours
- Overall weighted pace: approximately 7:09 /km

The raw Strava export contains 185 activities covering 9 Nov 2025 - 22 Jul 2026.

The first and last analysis months are partial observation periods, so monthly comparisons should be interpreted with that limitation in mind.

## Project Architecture

The V2 analytical flow is:

```text
Sanitized V1 CSV
        |
        v
DuckDB table
        |
        v
SQL analytical views
        |
        v
Python query layer
        |
        v
Streamlit dashboard
        |
        v
Plotly charts and ranked tables
```

The dashboard initializes DuckDB in memory from the committed sanitized dataset and SQL scripts.

It does not require the local `strava_running.duckdb` development database.


## Dataset and Privacy

The canonical V2 analytical input is:

`data/processed/activities_run_clean.csv`

This dataset contains sanitized running activity data prepared and validated in V1.

The public analytical dataset excludes:

- Raw Strava export files
- Original Strava activity identifiers
- Original filenames
- Precise GPS data
- Profile information
- Login information
- Device identifiers

The raw Strava export is stored locally under `data/raw/` and is intentionally excluded from Git.

The analytical `activity_id` field is a surrogate identifier generated for this project. It is not the original Strava Activity ID.

## Metric Definitions

### Distance

Canonical running distance:

`distance_km = Distance.1 / 1000`

`Distance.1` contains the more precise meter-level distance from the source export used during V1 preparation.

### Activity Pace

Activity-level running pace is calculated as:

`pace_min_km = (moving_time_sec / 60) / distance_km`

### Weighted Pace

Overall and grouped running pace are calculated using:

`total moving time / total distance`

This is a distance-weighted pace calculation.

The project does not calculate aggregate pace by taking a simple mean of activity-level pace because doing so would give equal weight to runs of different distances.


## V1 — Exploratory Running Analysis

V1 establishes the cleaned analytical dataset, KPI definitions, data-quality checks, and exploratory visual analysis using Python and Pandas.

The V1 notebook includes:

- Overall running KPI summary
- Monthly running distance
- Monthly running frequency
- Monthly weighted pace
- Running distance distribution
- Running frequency by weekday
- Distance vs running pace
- Top 10 longest runs
- Cumulative running distance

### V1 Notebook

`notebooks/v1_running_analysis.ipynb`

### V1 Processed Data

- `data/processed/activities_run_clean.csv`
- `data/processed/monthly_running_summary.csv`
- `data/processed/v1_summary_metrics.csv`
- `data/processed/v1_data_quality_report.csv`

### V1 Charts

Charts are stored in:

`images/charts/`

## V2 — SQL Analytics

V2 uses DuckDB to rebuild the analytical environment from the sanitized V1 CSV.

The SQL layer includes:

- Explicit table schema and typed CSV loading
- KPI reconciliation against the V1 baseline
- Monthly aggregation
- Weekday aggregation
- Distance categories using `CASE WHEN`
- Ranked longest runs using `ROW_NUMBER()`
- Run-level analytical data for interactive filtering

The analytical database contains one base table and six views:

- `activities_run`
- `v_kpi_summary`
- `v_monthly_summary`
- `v_weekday_summary`
- `v_distance_category`
- `v_longest_runs`
- `v_run_details`

SQL scripts are stored in:

`sql/`


## V2 — Python Query Layer

Reusable DuckDB access functions are implemented in:

`dashboard/queries.py`

The query layer is responsible for:

- Initializing the in-memory DuckDB database
- Executing the SQL scripts
- Returning dashboard-ready Pandas DataFrames
- Supporting parameterized month filtering
- Preserving the weighted-pace calculation contract
- Recalculating longest-run ranking after filtering

Using `year_month=None` preserves the full-dataset behavior.

Supplying a value such as `year_month="2026-01"` recalculates filtered KPIs and analytical summaries in DuckDB SQL.

## V2 — Interactive Dashboard

The Streamlit application is:

`app.py`

The dashboard contains:

- Four KPI cards
- Monthly running distance
- Monthly weighted pace
- Runs by day of week
- Distance-category distribution
- Ranked longest-runs table
- Interactive analysis-month selector

The KPI cards display:

- Total distance
- Number of runs
- Overall weighted pace
- Longest run

### Month Filtering

The dashboard supports an `All Months` view and individual analysis months from Nov 2025 through Jul 2026.

When one month is selected, DuckDB recalculates:

- KPI cards
- Weekday running patterns
- Distance categories
- Longest-run rankings

The monthly distance and monthly weighted-pace charts intentionally remain on the full analysis period so the selected month can still be interpreted within its broader temporal context.

For example, January 2026 contains:

- 22 runs
- 209.19 km total distance
- 9.51 km average run distance
- 21.01 km longest run
- 24.70 moving hours
- 7.0841 min/km weighted pace

The longest-run ranking is recalculated after filtering, so each selected month starts again at rank 1.


## Key Findings

- January 2026 recorded the highest monthly running distance at approximately 209.19 km.
- January 2026 also recorded the highest monthly run frequency with 22 runs.
- The fastest monthly weighted pace occurred in November 2025 at approximately 6:46 /km.
- Saturday was the most frequent running day, with 25 recorded runs.
- Medium-distance runs from 5 km to under 10 km were the most frequent distance category, with 53 runs.
- The longest recorded run was approximately 23.60 km.

## Technology Stack

- Python 3.12
- Pandas 3.0.5
- DuckDB 1.5.5
- Streamlit 1.62.0
- Plotly 7.0.0
- Git

## Project Structure

```text
strava-running-analysis/
|
|-- app.py
|-- README.md
|-- requirements.txt
|
|-- dashboard/
|   |-- __init__.py
|   `-- queries.py
|
|-- data/
|   |-- processed/
|   |   |-- activities_run_clean.csv
|   |   |-- monthly_running_summary.csv
|   |   |-- v1_data_quality_report.csv
|   |   `-- v1_summary_metrics.csv
|   |
|   `-- raw/
|       `-- private and Git-ignored
|
|-- images/
|   `-- charts/
|
|-- notebooks/
|   `-- v1_running_analysis.ipynb
|
|-- sql/
|   |-- 01_create_table.sql
|   |-- 02_kpi_queries.sql
|   `-- 03_dashboard_views.sql
|
`-- documents/
```


## Installation

The project was developed and tested with Python 3.12.

Create and activate a virtual environment:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

Install the pinned dependencies:

```bash
pip install -r requirements.txt
```

## Run the Dashboard

Run Streamlit from the repository root:

```bash
streamlit run app.py
```

The application builds an in-memory DuckDB analytical database from:

`data/processed/activities_run_clean.csv`

and the SQL scripts under:

`sql/`

A persistent local DuckDB database is not required to run the dashboard.

## Reproducibility

The V2 application rebuilds its analytical environment from committed project artifacts:

```text
activities_run_clean.csv
        +
01_create_table.sql
        +
02_kpi_queries.sql
        +
03_dashboard_views.sql
        |
        v
In-memory DuckDB analytical database
```

The analytical workflow has been reconciled against the V1 baseline:

- Runs: 126
- Total distance: 1,065.91 km
- Longest run: 23.60 km
- Total moving time: 126.92 hours
- Overall weighted pace: 7.1445 min/km, approximately 7:09 /km

The application does not require the raw Strava export or the local `strava_running.duckdb` development database.


## Version Progression

- V1 — Python / Pandas exploratory running analysis
- V2 — DuckDB SQL + Streamlit + Plotly interactive dashboard
- V3+ — Progressive analytical extensions

V1 is preserved with the Git tag:

`v1.0-basic-eda`

## Limitations

- The analysis covers one personal running dataset and should not be generalized to other runners.
- November 2025 and July 2026 are partial observation months.
- The dashboard focuses on descriptive running analytics rather than training prescriptions or causal conclusions.
- The sanitized public dataset intentionally excludes raw private Strava information.
- Monthly dashboard filtering is intentionally limited to keep V2 focused and interpretable.

## Future Extensions

Future versions may extend the project into areas such as:

- Training consistency analysis
- Running performance analysis
- Additional data-quality assessment
- Advanced analytical extensions

These extensions are intentionally separated from V2 so the current release remains focused on a clear SQL-to-dashboard analytics workflow.

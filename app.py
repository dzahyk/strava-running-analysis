"""
Streamlit dashboard for Strava Running Analysis V2.

Data flow:
    sanitized CSV
        -> DuckDB SQL
        -> analytical views
        -> dashboard query layer
        -> Streamlit + Plotly
"""

import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard.queries import (
    get_distance_categories,
    get_kpi_summary,
    get_longest_runs,
    get_monthly_summary,
    get_weekday_summary,
    initialize_database,
)


# ------------------------------------------------------------
# Page configuration
# ------------------------------------------------------------

st.set_page_config(
    page_title="Strava Running Analysis",
    page_icon="🏃",
    layout="wide",
)


# ------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------

def format_pace(pace_min_km: float) -> str:
    """
    Convert decimal pace in minutes/km to M:SS /km.

    Example:
        7.1445 -> 7:09 /km
    """
    minutes = int(pace_min_km)
    seconds = round((pace_min_km - minutes) * 60)

    if seconds == 60:
        minutes += 1
        seconds = 0

    return f"{minutes}:{seconds:02d} /km"


@st.cache_data
def load_dashboard_data():
    """
    Build the in-memory DuckDB database and return dashboard data.

    Only Pandas DataFrames are cached. The DuckDB connection is
    closed immediately after the required data is loaded.
    """
    connection = initialize_database()

    try:
        kpi_df = get_kpi_summary(connection)
        monthly_df = get_monthly_summary(connection)
        weekday_df = get_weekday_summary(connection)
        category_df = get_distance_categories(connection)
        longest_df = get_longest_runs(
            connection,
            limit=10,
        )

        return (
            kpi_df,
            monthly_df,
            weekday_df,
            category_df,
            longest_df,
        )

    finally:
        connection.close()


# ------------------------------------------------------------
# Load data
# ------------------------------------------------------------

(
    kpi_df,
    monthly_df,
    weekday_df,
    category_df,
    longest_df,
) = load_dashboard_data()

if kpi_df.empty:
    st.error("KPI data could not be loaded.")
    st.stop()

if monthly_df.empty:
    st.error("Monthly running data could not be loaded.")
    st.stop()

if weekday_df.empty:
    st.error("Weekday running data could not be loaded.")
    st.stop()

if category_df.empty:
    st.error("Distance category data could not be loaded.")
    st.stop()

if longest_df.empty:
    st.error("Longest-run data could not be loaded.")
    st.stop()

kpi = kpi_df.iloc[0]


# ------------------------------------------------------------
# Dashboard header
# ------------------------------------------------------------

st.title("🏃 Strava Running Analysis")

st.caption(
    "V2 interactive dashboard powered by DuckDB SQL, "
    "Streamlit, Plotly, and a sanitized running dataset."
)

start_date = pd.to_datetime(kpi["start_date"]).strftime("%d %b %Y")
end_date = pd.to_datetime(kpi["end_date"]).strftime("%d %b %Y")

st.write(f"**Analysis period:** {start_date} — {end_date}")


# ------------------------------------------------------------
# KPI cards
# ------------------------------------------------------------

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Total Distance",
        value=f"{float(kpi['total_distance_km']):,.2f} km",
    )

with col2:
    st.metric(
        label="Runs",
        value=f"{int(kpi['total_runs']):,}",
    )

with col3:
    st.metric(
        label="Overall Weighted Pace",
        value=format_pace(float(kpi["weighted_pace_min_km"])),
    )

with col4:
    st.metric(
        label="Longest Run",
        value=f"{float(kpi['longest_run_km']):.2f} km",
    )


st.divider()


# ------------------------------------------------------------
# Monthly running analysis
# ------------------------------------------------------------

st.subheader("Monthly Running Analysis")

monthly_chart_col1, monthly_chart_col2 = st.columns(2)


# Monthly distance chart
with monthly_chart_col1:

    monthly_distance_fig = px.bar(
        monthly_df,
        x="year_month",
        y="total_distance_km",
        title="Monthly Running Distance",
        labels={
            "year_month": "Month",
            "total_distance_km": "Distance (km)",
        },
        hover_data={
            "year_month": False,
            "total_distance_km": ":.2f",
            "total_runs": True,
        },
    )

    monthly_distance_fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Distance (km)",
        hovermode="x unified",
    )

    st.plotly_chart(
        monthly_distance_fig,
        width="stretch",
    )


# Monthly weighted pace chart
with monthly_chart_col2:

    monthly_pace_df = monthly_df.copy()

    monthly_pace_df["pace_display"] = (
        monthly_pace_df["weighted_pace_min_km"]
        .apply(format_pace)
    )

    monthly_pace_fig = px.line(
        monthly_pace_df,
        x="year_month",
        y="weighted_pace_min_km",
        markers=True,
        title="Monthly Weighted Pace",
        labels={
            "year_month": "Month",
            "weighted_pace_min_km": "Pace (min/km)",
        },
        hover_data={
            "year_month": False,
            "weighted_pace_min_km": ":.4f",
            "pace_display": True,
            "total_runs": True,
            "total_distance_km": ":.2f",
        },
    )

    monthly_pace_fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Pace (min/km)",
        hovermode="x unified",
    )

    st.plotly_chart(
        monthly_pace_fig,
        width="stretch",
    )

    st.caption(
        "Lower pace values indicate faster running. "
        "Monthly pace uses total moving time divided by total distance."
    )


st.divider()


# ------------------------------------------------------------
# Running pattern analysis
# ------------------------------------------------------------

st.subheader("Running Patterns")

pattern_col1, pattern_col2 = st.columns(2)


# Runs by day of week
with pattern_col1:

    weekday_chart_df = weekday_df.copy()

    weekday_chart_df["pace_display"] = (
        weekday_chart_df["weighted_pace_min_km"]
        .apply(format_pace)
    )

    weekday_order = weekday_chart_df["day_name"].tolist()

    weekday_fig = px.bar(
        weekday_chart_df,
        x="day_name",
        y="total_runs",
        title="Runs by Day of Week",
        category_orders={
            "day_name": weekday_order,
        },
        labels={
            "day_name": "Day",
            "total_runs": "Runs",
            "total_distance_km": "Distance (km)",
            "pace_display": "Weighted Pace",
        },
        hover_data={
            "day_name": False,
            "total_runs": True,
            "total_distance_km": ":.2f",
            "pace_display": True,
            "weighted_pace_min_km": False,
        },
    )

    weekday_fig.update_layout(
        xaxis_title="Day",
        yaxis_title="Runs",
        hovermode="x unified",
    )

    st.plotly_chart(
        weekday_fig,
        width="stretch",
    )


# Distance category distribution
with pattern_col2:

    category_chart_df = category_df.copy()

    category_chart_df["pace_display"] = (
        category_chart_df["weighted_pace_min_km"]
        .apply(format_pace)
    )

    category_order = (
        category_chart_df["distance_category"]
        .tolist()
    )

    category_fig = px.bar(
        category_chart_df,
        x="distance_category",
        y="total_runs",
        title="Distance Category Distribution",
        category_orders={
            "distance_category": category_order,
        },
        labels={
            "distance_category": "Distance Category",
            "total_runs": "Runs",
            "total_distance_km": "Distance (km)",
            "average_distance_km": "Average Distance (km)",
            "pace_display": "Weighted Pace",
        },
        hover_data={
            "distance_category": False,
            "total_runs": True,
            "total_distance_km": ":.2f",
            "average_distance_km": ":.2f",
            "pace_display": True,
            "weighted_pace_min_km": False,
            "category_order": False,
        },
    )

    category_fig.update_layout(
        xaxis_title="Distance Category",
        yaxis_title="Runs",
        hovermode="x unified",
    )

    st.plotly_chart(
        category_fig,
        width="stretch",
    )


st.divider()


# ------------------------------------------------------------
# Top running performances
# ------------------------------------------------------------

st.subheader("Top 10 Longest Runs")

longest_display_df = longest_df.copy()

longest_display_df["Date"] = (
    pd.to_datetime(longest_display_df["activity_date"])
    .dt.strftime("%d %b %Y")
)

longest_display_df["Pace"] = (
    longest_display_df["pace_min_km"]
    .apply(format_pace)
)

longest_display_df["Distance (km)"] = (
    longest_display_df["distance_km"]
    .round(2)
)

longest_display_df["Elevation Gain (m)"] = (
    longest_display_df["elevation_gain_m"]
    .round(1)
)

longest_display_df["Rank"] = (
    longest_display_df["distance_rank"]
    .astype(int)
)

longest_display_df["Day"] = (
    longest_display_df["day_name"]
)

longest_display_df = longest_display_df[
    [
        "Rank",
        "Date",
        "Day",
        "Distance (km)",
        "Pace",
        "Elevation Gain (m)",
    ]
]

st.dataframe(
    longest_display_df,
    width="stretch",
    hide_index=True,
    column_config={
        "Rank": st.column_config.NumberColumn(
            "Rank",
            format="%d",
        ),
        "Distance (km)": st.column_config.NumberColumn(
            "Distance (km)",
            format="%.2f",
        ),
        "Elevation Gain (m)": st.column_config.NumberColumn(
            "Elevation Gain (m)",
            format="%.1f",
        ),
    },
)

st.caption(
    "Runs are ranked by distance using the SQL "
    "ROW_NUMBER() window function."
)


st.divider()

st.caption(
    "The dashboard uses the sanitized V1 analytical dataset. "
    "Raw Strava export data is not used by the application."
)

"""
Streamlit dashboard for Strava Running Analysis V2.

Data flow:
    sanitized CSV
        -> DuckDB SQL
        -> analytical views
        -> dashboard query layer
        -> Streamlit + Plotly
"""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard.queries import (
    get_available_months,
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

# V2.2 monthly distance target state
DEFAULT_MONTHLY_DISTANCE_TARGET_KM = 150.0

st.session_state.setdefault(
    "monthly_distance_target_km",
    DEFAULT_MONTHLY_DISTANCE_TARGET_KM,
)


# V2.2 distance category cross-filter state
DISTANCE_CATEGORY_OPTIONS = (
    "Short",
    "Medium",
    "Long",
    "Very Long",
)

st.session_state.setdefault(
    "distance_category_filter",
    None,
)


st.session_state.setdefault(
    "distance_category_chart_version",
    0,
)

# V2.3 dynamic feedback state
st.session_state.setdefault(
    "v23_pending_toast",
    None,
)

st.session_state.setdefault(
    "v23_initial_data_loaded",
    False,
)

st.session_state.setdefault(
    "v23_entrance_complete",
    False,
)


# Normalize invalid category state
if (
    st.session_state["distance_category_filter"] is not None
    and st.session_state["distance_category_filter"]
    not in DISTANCE_CATEGORY_OPTIONS
):
    st.session_state["distance_category_filter"] = None



# ------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------

def load_css() -> None:
    """Load the external V2.1 dashboard stylesheet."""
    css_path = Path(__file__).resolve().parent / "style.css"
    css = css_path.read_text(encoding="utf-8")

    st.markdown(
        f"<style>{css}</style>",
        unsafe_allow_html=True,
    )


def format_month_option(value: str) -> str:
    """Convert YYYY-MM month values to a readable label."""
    if value == "All Months":
        return value

    return pd.to_datetime(
        f"{value}-01"
    ).strftime("%B %Y")


# ------------------------------------------------------------
# V2.3 interaction feedback helpers
# ------------------------------------------------------------

def queue_toast(message: str) -> None:
    """Queue one transient message for the next render."""
    st.session_state["v23_pending_toast"] = message


def show_pending_toast() -> None:
    """Render and consume the current transient message."""
    message = st.session_state.pop(
        "v23_pending_toast",
        None,
    )

    if message:
        st.toast(
            message,
            duration=3,
        )


def handle_month_change() -> None:
    """Provide feedback after the analysis month changes."""
    selected = st.session_state["analysis_month"]

    queue_toast(
        "Analysis updated · "
        + format_month_option(selected)
    )


def handle_target_change() -> None:
    """Provide feedback after the monthly target changes."""
    target = float(
        st.session_state[
            "monthly_distance_target_km"
        ]
    )

    queue_toast(
        f"Monthly target updated · {target:,.0f} km"
    )


# ------------------------------------------------------------
# V2.1 Plotly visual system
# ------------------------------------------------------------

CHART_TEXT_PRIMARY = "#F8FAFC"
CHART_TEXT_SECONDARY = "#CBD5E1"
CHART_TEXT_MUTED = "#94A3B8"

CHART_GRID = "rgba(148, 163, 184, 0.10)"
CHART_AXIS = "rgba(148, 163, 184, 0.18)"

CHART_ORANGE = "#FC4C02"
CHART_INDIGO = "#6366F1"
CHART_PURPLE = "#A78BFA"
CHART_TEAL = "#14B8A6"
CHART_CYAN = "#22D3EE"

CHART_TRANSPARENT = "rgba(0, 0, 0, 0)"



# V2.3 Plotly interaction configuration
PLOTLY_CONFIG = {
    "displaylogo": False,
    "responsive": True,
    "scrollZoom": False,
    "displayModeBar": "hover",
    "doubleClick": "reset+autosize",
    "showTips": False,
    "modeBarButtonsToRemove": [
        "lasso2d",
        "select2d",
        "autoScale2d",
    ],
}

def apply_chart_theme(
    fig,
    *,
    show_y_grid: bool = True,
    uirevision: str = "v23",
    time_series: bool = False,
) -> None:
    """Apply the shared V2.3 Midnight Athletic Plotly styling."""
    fig.update_layout(
        paper_bgcolor=CHART_TRANSPARENT,
        plot_bgcolor=CHART_TRANSPARENT,
        font=dict(
            family="Inter, system-ui, sans-serif",
            color=CHART_TEXT_SECONDARY,
            size=12,
        ),
        title=dict(
            font=dict(
                color=CHART_TEXT_PRIMARY,
                size=18,
            ),
            x=0.02,
            xanchor="left",
        ),
        margin=dict(
            l=24,
            r=20,
            t=64,
            b=24,
        ),
        hoverlabel=dict(
            bgcolor="#0F172A",
            bordercolor="rgba(34, 211, 238, 0.24)",
            font=dict(
                family="Inter, system-ui, sans-serif",
                color=CHART_TEXT_PRIMARY,
                size=12,
            ),
            align="left",
            namelength=-1,
        ),
        legend=dict(
            orientation="h",
            x=0,
            y=1.06,
            xanchor="left",
            yanchor="bottom",
            bgcolor=CHART_TRANSPARENT,
            font=dict(
                color=CHART_TEXT_MUTED,
                size=11,
            ),
            itemclick="toggle",
            itemdoubleclick="toggleothers",
        ),
        transition=dict(
            duration=280,
            easing="cubic-in-out",
        ),
        uirevision=uirevision,
        hoverdistance=80,
    )

    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        showline=True,
        linecolor=CHART_AXIS,
        tickfont=dict(
            color=CHART_TEXT_MUTED,
        ),
        title_font=dict(
            color=CHART_TEXT_MUTED,
        ),
    )

    fig.update_yaxes(
        showgrid=show_y_grid,
        gridcolor=CHART_GRID,
        gridwidth=1,
        zeroline=False,
        showline=False,
        tickfont=dict(
            color=CHART_TEXT_MUTED,
        ),
        title_font=dict(
            color=CHART_TEXT_MUTED,
        ),
    )

    if time_series:
        fig.update_layout(
            hovermode="x unified",
            spikedistance=-1,
        )

        fig.update_xaxes(
            showspikes=True,
            spikemode="across",
            spikesnap="cursor",
            spikecolor="rgba(34, 211, 238, 0.48)",
            spikethickness=1,
            spikedash="dot",
        )


def render_kpi_card(
    label: str,
    value: str,
    meta: str,
    accent_class: str,
) -> None:
    """Render a reusable V2.1 KPI card."""
    st.markdown(
        (
            f'<div class="kpi-card {accent_class}">'
            f'<div class="kpi-label">{label}</div>'
            f'<p class="kpi-value">{value}</p>'
            f'<div class="kpi-meta">{meta}</div>'
            '</div>'
        ),
        unsafe_allow_html=True,
    )


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
def load_available_month_options() -> list[str]:
    """Return available dashboard months."""
    connection = initialize_database()

    try:
        return get_available_months(connection)
    finally:
        connection.close()


def load_dashboard_data(
    year_month: str | None,
    distance_category: str | None = None,
):
    """
    Build the in-memory DuckDB database and return dashboard data.

    Monthly trends remain unfiltered for temporal context.
    KPI, weekday, and ranked-run data respect the active month
    and optional distance-category cross-filter.

    The category distribution itself remains month-filtered only
    so all categories stay available for interactive selection.
    """
    connection = initialize_database()

    try:
        kpi_df = get_kpi_summary(
            connection,
            year_month=year_month,
            distance_category=distance_category,
        )

        monthly_df = get_monthly_summary(
            connection,
        )

        weekday_df = get_weekday_summary(
            connection,
            year_month=year_month,
            distance_category=distance_category,
        )

        category_df = get_distance_categories(
            connection,
            year_month=year_month,
        )

        longest_df = get_longest_runs(
            connection,
            limit=10,
            year_month=year_month,
            distance_category=distance_category,
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
# Dashboard header and month filter
# ------------------------------------------------------------

load_css()

# Entrance motion belongs to the first page render only.
if st.session_state["v23_entrance_complete"]:
    st.markdown(
        """
        <style>
        .app-eyebrow,
        .app-title,
        .app-subtitle,
        .kpi-card,
        div[data-testid="stPlotlyChart"],
        div[data-testid="stDataFrame"] {
            animation: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

available_months = load_available_month_options()

month_options = [
    "All Months",
    *available_months,
]

header_col, filter_col = st.columns(
    [3.2, 1.0],
    gap="large",
)

with header_col:
    st.markdown(
        """
        <div class="app-eyebrow">
            Running Analytics · V2.3
        </div>

        <h1 class="app-title">
            Strava Running
            <span class="app-title-gradient">Analysis</span>
        </h1>

        <p class="app-subtitle">
            Personal running intelligence powered by DuckDB SQL,
            Streamlit, Plotly, and a sanitized analytical dataset.
        </p>
        """,
        unsafe_allow_html=True,
    )

with filter_col:
    filter_placeholder = st.empty()


# ------------------------------------------------------------
# V2.3 anti-flicker interactive fragment
# ------------------------------------------------------------

@st.fragment
def render_interactive_dashboard() -> None:
    """
    Render interactive dashboard content independently.

    Month, target, and category interactions rerun this
    fragment instead of the complete Streamlit application.
    """

    with filter_placeholder.container():
        st.markdown(
            '<div class="app-eyebrow">Analysis Control</div>',
            unsafe_allow_html=True,
        )

        selected_month = st.selectbox(
            "Analysis Month",
            options=month_options,
            index=0,
            format_func=format_month_option,
            key="analysis_month",
            on_change=handle_month_change,
        )

    # Callbacks may queue feedback before a fragment rerun.
    show_pending_toast()

    selected_year_month = (
        None
        if selected_month == "All Months"
        else selected_month
    )


    # ------------------------------------------------------------
    # Load dashboard data
    # ------------------------------------------------------------

    initial_data_load = not st.session_state[
        "v23_initial_data_loaded"
    ]

    loading_placeholder = st.empty()

    if initial_data_load:
        loading_placeholder.markdown(
            """
            <div class="v23-loading-shell">
                <div class="v23-loading-meta">
                    Preparing your running intelligence
                </div>

                <div class="v23-skeleton-kpis">
                    <div class="v23-skeleton-card"></div>
                    <div class="v23-skeleton-card"></div>
                    <div class="v23-skeleton-card"></div>
                    <div class="v23-skeleton-card"></div>
                </div>

                <div class="v23-skeleton-charts">
                    <div class="v23-skeleton-chart"></div>
                    <div class="v23-skeleton-chart"></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    (
        kpi_df,
        monthly_df,
        weekday_df,
        category_df,
        longest_df,
    ) = load_dashboard_data(
        selected_year_month,
        st.session_state["distance_category_filter"],
    )

    if initial_data_load:
        loading_placeholder.empty()

        st.session_state[
            "v23_initial_data_loaded"
        ] = True

        st.toast(
            "Dashboard ready · running data loaded",
            duration=2,
        )

    if kpi_df.empty:
        active_empty_category = st.session_state[
            "distance_category_filter"
        ]

        st.markdown(
            """
            <div class="v23-empty-state">
                <div class="v23-empty-icon">↗</div>

                <div class="v23-empty-eyebrow">
                    NO MATCHING RUNS
                </div>

                <h3>
                    This analysis view has no activities
                </h3>

                <p>
                    Try another month or clear the active
                    distance-category filter to continue exploring.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if active_empty_category is not None:
            if st.button(
                "Clear category filter",
                key="empty_state_clear_category",
                type="primary",
            ):
                st.session_state[
                    "distance_category_filter"
                ] = None

                st.session_state[
                    "distance_category_chart_version"
                ] += 1

                queue_toast(
                    "Category filter cleared"
                )

                st.rerun(scope="fragment")

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
    # Active analysis context
    # ------------------------------------------------------------

    start_date = pd.to_datetime(
        kpi["start_date"]
    ).strftime("%d %b %Y")

    end_date = pd.to_datetime(
        kpi["end_date"]
    ).strftime("%d %b %Y")

    view_label = format_month_option(
        selected_month
    )

    st.markdown(
        (
            '<div class="analysis-context">'
            f'<span class="context-pill context-pill-accent">'
            f'VIEW · {view_label.upper()}'
            '</span>'
            f'<span class="context-pill">'
            f'PERIOD · {start_date.upper()} — {end_date.upper()}'
            '</span>'
            '</div>'
        ),
        unsafe_allow_html=True,
    )

    if selected_year_month is not None:
        st.markdown(
            """
            <div class="dashboard-note">
                <span class="dashboard-note-icon">ℹ️</span>
                <span>
                    KPI cards, running patterns, and ranked runs reflect
                    the selected month. Monthly trend charts remain on
                    the full analysis period to preserve temporal context.
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )


    # ------------------------------------------------------------
    # KPI cards
    # ------------------------------------------------------------

    # V2.2 active cross-filter context
    active_distance_category = st.session_state[
        "distance_category_filter"
    ]

    if active_distance_category is not None:
        st.markdown(
            f"""
            <div class="cross-filter-status">
                <span class="cross-filter-status-label">
                    ACTIVE CATEGORY
                </span>
                <span class="cross-filter-status-value">
                    {active_distance_category.upper()}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(
        4,
        gap="medium",
    )

    with kpi_col1:
        render_kpi_card(
            label="Total Distance",
            value=f"{float(kpi['total_distance_km']):,.2f} km",
            meta="Across the selected analysis period",
            accent_class="kpi-distance",
        )

    with kpi_col2:
        render_kpi_card(
            label="Runs",
            value=f"{int(kpi['total_runs']):,}",
            meta="Recorded running activities",
            accent_class="kpi-runs",
        )

    with kpi_col3:
        render_kpi_card(
            label="Weighted Pace",
            value=format_pace(
                float(kpi["weighted_pace_min_km"])
            ),
            meta="Total moving time ÷ total distance",
            accent_class="kpi-pace",
        )

    with kpi_col4:
        render_kpi_card(
            label="Longest Run",
            value=f"{float(kpi['longest_run_km']):.2f} km",
            meta="Maximum activity distance",
            accent_class="kpi-longest",
        )


    st.markdown(
        '<div class="section-divider"></div>',
        unsafe_allow_html=True,
    )


    # ------------------------------------------------------------
    # Monthly running analysis
    # ------------------------------------------------------------

    st.markdown(
        (
            '<div class="section-kicker">Performance Trends</div>'
            '<h2 class="section-heading">'
            'Monthly Running Analysis'
            '</h2>'
            '<p class="section-description">'
            'Track monthly training volume and weighted pace '
            'across the full analysis period.'
            '</p>'
        ),
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="chart-control-label">
            MONTHLY DISTANCE TARGET
        </div>
        <div class="chart-control-help">
            Personal goal · km/month
        </div>
        """,
        unsafe_allow_html=True,
    )

    monthly_distance_target_km = st.number_input(
        "Monthly distance target",
        min_value=25.0,
        max_value=500.0,
        step=5.0,
        format="%.0f",
        key="monthly_distance_target_km",
        on_change=handle_target_change,
        help=(
            "Sets the horizontal reference line on Monthly Running Distance. "
            "This personal target does not change analytics or filters."
        ),
        label_visibility="collapsed",
    )

    monthly_chart_col1, monthly_chart_col2 = st.columns(
        2,
        gap="large",
    )


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
            custom_data=[
                "total_runs",
            ],
            color_discrete_sequence=[
                CHART_INDIGO,
            ],
        )

        max_monthly_distance = (
            monthly_df["total_distance_km"].max()
        )

        monthly_distance_colors = [
            (
                CHART_ORANGE
                if distance == max_monthly_distance
                else "#475569"
            )
            for distance in monthly_df["total_distance_km"]
        ]

        monthly_distance_fig.update_traces(
            marker=dict(
                color=monthly_distance_colors,
                line=dict(
                    width=0,
                ),
            ),
            opacity=0.94,
            hovertemplate=(
                "<b>%{x}</b>"
                "<br>Distance: %{y:.2f} km"
                "<br>Runs: %{customdata[0]:.0f}"
                "<extra></extra>"
            ),
        )

        monthly_distance_fig.update_layout(
            xaxis_title="Month",
            yaxis_title="Distance (km)",
            hovermode="closest",
            bargap=0.32,
            barcornerradius=6,
        )

        # V2.2 dynamic monthly distance target line
        monthly_distance_y_max = max(
            float(max_monthly_distance),
            float(monthly_distance_target_km),
        ) * 1.12

        monthly_distance_fig.add_hline(
            y=monthly_distance_target_km,
            line_width=1.7,
            line_dash="dash",
            line_color="#FC4C02",
            opacity=0.92,
            annotation_text=(
                f"Target · {monthly_distance_target_km:,.0f} km"
            ),
            annotation_position="top right",
            annotation_font_size=11,
            annotation_font_color="#FDBA74",
        )

        monthly_distance_fig.update_yaxes(
            range=[0, monthly_distance_y_max],
        )


        apply_chart_theme(
            monthly_distance_fig,
            uirevision="monthly-distance-v23",
        )

        st.plotly_chart(
            monthly_distance_fig,
            width="stretch",
            key="monthly_distance_chart_v23",
            config=PLOTLY_CONFIG,
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
            custom_data=[
                "pace_display",
                "total_runs",
                "total_distance_km",
            ],
        )

        monthly_pace_fig.update_traces(
            mode="lines+markers",
            line=dict(
                color=CHART_PURPLE,
                width=3,
                shape="spline",
                smoothing=1.2,
            ),
            marker=dict(
                size=8,
                color=CHART_PURPLE,
                line=dict(
                    color="#E2E8F0",
                    width=1.4,
                ),
            ),
            fill="tozeroy",
            fillcolor="rgba(167, 139, 250, 0.08)",
            hovertemplate=(
                "<b>%{x}</b>"
                "<br>Weighted Pace: %{customdata[0]}"
                "<br>Runs: %{customdata[1]:.0f}"
                "<br>Distance: %{customdata[2]:.2f} km"
                "<extra></extra>"
            ),
        )

        overall_weighted_pace = (
            (
                monthly_pace_df["weighted_pace_min_km"]
                * monthly_pace_df["total_distance_km"]
            ).sum()
            / monthly_pace_df["total_distance_km"].sum()
        )

        pace_min = monthly_pace_df[
            "weighted_pace_min_km"
        ].min()

        pace_max = monthly_pace_df[
            "weighted_pace_min_km"
        ].max()

        pace_padding = max(
            (pace_max - pace_min) * 0.18,
            0.08,
        )

        monthly_pace_fig.update_layout(
            xaxis_title="Month",
            yaxis_title="Pace (min/km)",
            hovermode="x unified",
        )

        monthly_pace_fig.update_yaxes(
            range=[
                pace_min - pace_padding,
                pace_max + pace_padding,
            ],
        )



        monthly_pace_fig.add_hline(
            y=overall_weighted_pace,
            line_width=1,
            line_dash="dot",
            line_color="rgba(252, 76, 2, 0.70)",
            annotation_text=(
                "Overall · "
                f"{format_pace(overall_weighted_pace)}"
            ),
            annotation_position="top left",
            annotation_font=dict(
                color=CHART_TEXT_MUTED,
                size=11,
            ),
        )

        apply_chart_theme(
            monthly_pace_fig,
            uirevision="monthly-pace-v23",
            time_series=True,
        )

        st.plotly_chart(
            monthly_pace_fig,
            width="stretch",
            key="monthly_pace_chart_v23",
            config=PLOTLY_CONFIG,
        )

        st.caption(
            "Lower pace values indicate faster running. "
            "Monthly pace uses total moving time divided by total distance."
        )


    st.markdown(
        '<div class="section-divider"></div>',
        unsafe_allow_html=True,
    )


    # ------------------------------------------------------------
    # Running pattern analysis
    # ------------------------------------------------------------

    st.markdown(
        (
            '<div class="section-kicker">Running Behavior</div>'
            '<h2 class="section-heading">'
            'Running Patterns'
            '</h2>'
            '<p class="section-description">'
            'Understand when runs happen most often and how '
            'activity distances are distributed.'
            '</p>'
        ),
        unsafe_allow_html=True,
    )

    pattern_col1, pattern_col2 = st.columns(
        2,
        gap="large",
    )


    # Runs by day of week
    with pattern_col1:

        weekday_chart_df = weekday_df.copy()

        weekday_chart_df["pace_display"] = (
            weekday_chart_df["weighted_pace_min_km"]
            .apply(format_pace)
        )

        weekday_order = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]

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
            },
            custom_data=[
                "total_distance_km",
                "pace_display",
            ],
        )

        max_weekday_runs = (
            weekday_chart_df["total_runs"].max()
        )

        weekday_colors = [
            (
                CHART_ORANGE
                if runs == max_weekday_runs
                else "#475569"
            )
            for runs in weekday_chart_df["total_runs"]
        ]

        weekday_fig.update_traces(
            marker=dict(
                color=weekday_colors,
                line=dict(
                    width=0,
                ),
            ),
            opacity=0.94,
            hovertemplate=(
                "<b>%{x}</b>"
                "<br>Runs: %{y:.0f}"
                "<br>Distance: %{customdata[0]:.2f} km"
                "<br>Weighted Pace: %{customdata[1]}"
                "<extra></extra>"
            ),
        )

        weekday_fig.update_layout(
            xaxis_title="Day",
            yaxis_title="Runs",
            hovermode="closest",
            bargap=0.30,
            barcornerradius=6,
        )

        apply_chart_theme(
            weekday_fig,
            uirevision="weekday-v23",
        )

        st.plotly_chart(
            weekday_fig,
            width="stretch",
            key="weekday_chart_v23",
            config=PLOTLY_CONFIG,
        )


    # Distance category distribution
    with pattern_col2:

        category_chart_df = category_df.copy()

        category_chart_df["pace_display"] = (
            category_chart_df["weighted_pace_min_km"]
            .apply(format_pace)
        )

        category_order = [
            "Short (<5 km)",
            "Medium (5-<10 km)",
            "Long (10-<15 km)",
            "Very Long (>=15 km)",
        ]

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
            },
            custom_data=[
                "total_distance_km",
                "average_distance_km",
                "pace_display",
            ],
        )

        max_category_runs = (
            category_chart_df["total_runs"].max()
        )

        category_colors = [
            (
                CHART_ORANGE
                if runs == max_category_runs
                else "#475569"
            )
            for runs in category_chart_df["total_runs"]
        ]

        category_fig.update_traces(
            marker=dict(
                color=category_colors,
                line=dict(
                    width=0,
                ),
            ),
            opacity=0.94,
            hovertemplate=(
                "<b>%{x}</b>"
                "<br>Runs: %{y:.0f}"
                "<br>Total Distance: %{customdata[0]:.2f} km"
                "<br>Average Distance: %{customdata[1]:.2f} km"
                "<br>Weighted Pace: %{customdata[2]}"
                "<extra></extra>"
            ),
        )

        category_fig.update_layout(
            xaxis_title="Distance Category",
            yaxis_title="Runs",
            hovermode="closest",
            bargap=0.32,
            barcornerradius=6,
        )

        apply_chart_theme(
            category_fig,
            uirevision="distance-category-v23",
        )

        # V2.2 native distance-category selection
        active_distance_category = st.session_state[
            "distance_category_filter"
        ]

        if active_distance_category is not None:
            category_fig.update_traces(
                marker_color=[
                    (
                        "#FC4C02"
                        if str(category_label).startswith(
                            active_distance_category
                        )
                        else "#475569"
                    )
                    for category_label in (
                        category_chart_df[
                            "distance_category"
                        ]
                    )
                ],
            )

            if st.button(
                "Clear category filter",
                key="clear_distance_category_filter",
                type="secondary",
            ):
                st.session_state[
                    "distance_category_filter"
                ] = None
                st.session_state[
                    "distance_category_chart_version"
                ] += 1

                queue_toast(
                    "Category filter cleared"
                )

                st.rerun(scope="fragment")

        st.markdown(
            """
            <div class="v23-interaction-hint">
                <span class="v23-interaction-hint-icon">↗</span>
                <span>
                    Click a distance bar to filter KPI,
                    weekday patterns, and ranked runs
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        category_selection = st.plotly_chart(
            category_fig,
            width="stretch",
            key=(
                "distance_category_cross_filter_"
                + str(
                    st.session_state[
                        "distance_category_chart_version"
                    ]
                )
            ),
            config=PLOTLY_CONFIG,
            on_select="rerun",
            selection_mode="points",
        )

        selected_points = (
            category_selection.selection.points
        )

        if selected_points:
            selected_point = selected_points[0]

            selection_values = [
                selected_point.get("x"),
                selected_point.get("y"),
            ]

            customdata = selected_point.get(
                "customdata"
            )

            if isinstance(
                customdata,
                (list, tuple),
            ):
                selection_values.extend(customdata)

            clicked_category = next(
                (
                    category
                    for category in DISTANCE_CATEGORY_OPTIONS
                    if any(
                        str(value).startswith(category)
                        for value in selection_values
                        if value is not None
                    )
                ),
                None,
            )

            if (
                clicked_category is not None
                and clicked_category
                != st.session_state[
                    "distance_category_filter"
                ]
            ):
                st.session_state[
                    "distance_category_filter"
                ] = clicked_category

                queue_toast(
                    f"Filtered to {clicked_category} runs"
                )

                st.rerun(scope="fragment")



    st.markdown(
        '<div class="section-divider"></div>',
        unsafe_allow_html=True,
    )


    # ------------------------------------------------------------
    # Top running performances
    # ------------------------------------------------------------

    st.markdown(
        (
            '<div class="section-kicker">Performance Ranking</div>'
            '<h2 class="section-heading">'
            f'Top {len(longest_df)} Longest Runs'
            '</h2>'
            '<p class="section-description">'
            'Review the longest running efforts in the active '
            'analysis view, ranked from highest to lowest distance.'
            '</p>'
        ),
        unsafe_allow_html=True,
    )

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

    st.markdown(
        (
            '<div class="table-context">'
            '<span class="table-context-pill">'
            f'{len(longest_display_df)} ranked activities'
            '</span>'
            '<span class="table-context-pill">'
            'Primary metric · Distance'
            '</span>'
            '</div>'
        ),
        unsafe_allow_html=True,
    )

    table_row_height = 36

    table_height = (
        42
        + (len(longest_display_df) * table_row_height)
        + 8
    )

    st.dataframe(
        longest_display_df,
        width="stretch",
        height=table_height,
        row_height=table_row_height,
        hide_index=True,
        column_config={
            "Rank": st.column_config.NumberColumn(
                "Rank",
                format="%d",
                width="small",
            ),
            "Date": st.column_config.TextColumn(
                "Date",
                width="medium",
            ),
            "Day": st.column_config.TextColumn(
                "Day",
                width="medium",
            ),
            "Distance (km)": st.column_config.NumberColumn(
                "Distance (km)",
                format="%.2f",
                width="medium",
            ),
            "Pace": st.column_config.TextColumn(
                "Pace",
                width="medium",
            ),
            "Elevation Gain (m)": st.column_config.NumberColumn(
                "Elevation Gain (m)",
                format="%.1f",
                width="medium",
            ),
        },
    )

    st.markdown(
        (
            '<div class="table-note">'
            'Ranking is generated in SQL with '
            '<strong>ROW_NUMBER()</strong> ordered by distance. '
            'The rank is recalculated after an active month filter '
            'so the displayed ordering always reflects the current view.'
            '</div>'
        ),
        unsafe_allow_html=True,
    )


render_interactive_dashboard()

# Subsequent Streamlit reruns should not replay
# the full-page entrance sequence.
st.session_state["v23_entrance_complete"] = True

st.markdown(
    (
        '<div class="dashboard-footer">'
        '🔒 <strong>Privacy by design.</strong> '
        'This dashboard uses the sanitized V1 analytical dataset. '
        'Raw Strava export data is not used by the application.'
        '</div>'
    ),
    unsafe_allow_html=True,
)

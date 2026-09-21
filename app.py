import os

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


st.set_page_config(
    page_title="UCLytics | Team Intelligence",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data
def load_matches():
    data = pd.read_csv(os.path.join(os.path.dirname(__file__), "data.csv"))
    data.columns = [column.strip() for column in data.columns]
    # Keep the app compatible with the original score-column naming.
    data = data.rename(columns={"Home Score": "Home Goals", "Away Score": "Away Goals"})
    data["Date"] = pd.to_datetime(data["Date"], dayfirst=True, errors="coerce")
    for column in ["Home Goals", "Away Goals"]:
        data[column] = pd.to_numeric(data[column], errors="coerce").fillna(0).astype(int)
    data["Score"] = data["Home Goals"].astype(str) + " - " + data["Away Goals"].astype(str)
    return data.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)



matches = load_matches()
teams = sorted(set(matches["Home Team"]).union(matches["Away Team"]))
rankings = power_rankings(matches)
rankings["Strength index"] = rankings.apply(strength_index, axis=1)
elos, elo_history = elo_ratings(matches)

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Space+Grotesk:wght@400;500;600;700&display=swap');

:root {
    --bg: #0b1011;
    --surface: #151c1d;
    --surface-2: #1c2425;
    --ink: #f5f5f0;
    --text-soft: #d0d5d2;
    --muted: #a5adaa;
    --line: #354041;
    --lime: #d9f36a;
    --coral: #ff836d;
}

/* MAIN BACKGROUND */
.stApp {
    background: var(--bg);
    color: var(--ink);
}

/* SIDEBAR */
[data-testid="stSidebar"] {
    background: #111718;
    border-right: 1px solid var(--line);
}

[data-testid="stSidebar"] * {
    color: var(--text-soft);
}

/* FONT */
[data-testid="stSidebar"] *,
h1, h2, h3, h4, p, label, .stMarkdown {
    font-family: 'Space Grotesk', sans-serif;
}

/* MAIN TITLE */
h1 {
    font-size: 3.2rem !important;
    line-height: 1.05 !important;
    letter-spacing: -0.04em !important;
    color: var(--ink) !important;
}

h2 {
    font-size: 1.45rem !important;
    color: var(--ink) !important;
    margin-top: 2rem !important;
}

/* SMALL GREEN LABEL */
.eyebrow {
    color: var(--lime);
    font-family: 'DM Mono', monospace;
    font-size: .72rem;
    font-weight: 500;
    letter-spacing: .14em;
    text-transform: uppercase;
    margin-bottom: .6rem;
}

/* DESCRIPTION */
.lede {
    color: var(--text-soft);
    font-size: 1rem;
    line-height: 1.5;
}

/* FORM */
.record {
    font-family: 'DM Mono', monospace;
    color: var(--muted);
}

.record strong {
    color: var(--lime);
    font-size: 1.15rem;
}

/* METRIC CARDS */
div[data-testid="stMetric"] {
    background: var(--surface) !important;
    border: 1px solid var(--line) !important;
    border-radius: 10px !important;
    padding: 1.15rem !important;
    min-height: 105px;
    box-shadow: 0 4px 14px rgba(0,0,0,.25);
}

div[data-testid="stMetricLabel"] {
    color: var(--muted) !important;
    font-size: .76rem !important;
    font-weight: 500 !important;
    text-transform: uppercase;
}

div[data-testid="stMetricValue"] {
    color: var(--ink) !important;
    font-size: 2rem !important;
    font-weight: 600 !important;
}

/* SELECT BOXES */
div[data-baseweb="select"] > div {
    background: var(--surface-2) !important;
    border: 1px solid var(--line) !important;
    border-radius: 8px !important;
}

div[data-baseweb="select"] span {
    color: var(--ink) !important;
}

/* SIDEBAR CAPTIONS */
[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
    color: var(--muted) !important;
}

/* DIVIDERS */
hr {
    border-color: var(--line) !important;
}

/* DATAFRAMES */
[data-testid="stDataFrame"] {
    border: 1px solid var(--line);
    border-radius: 8px;
    overflow: hidden;
}

/* PAGE WIDTH */
.block-container {
    max-width: 1450px;
    padding-top: 2.5rem;
    padding-bottom: 4rem;
}

</style>
""", unsafe_allow_html=True)

with st.sidebar:

    st.markdown(
        '<div class="eyebrow">UCLYTICS / 02</div>',
        unsafe_allow_html=True
    )

    st.markdown("## Team intelligence")

    st.caption(
        "Explore team performance, form and strength."
    )

    st.markdown("### Focus team")

    selected_team = st.selectbox(
        "Focus team",
        teams,
        index=teams.index("Real Madrid") if "Real Madrid" in teams else 0,
        label_visibility="collapsed"
    )

    st.markdown("### Compare against")

    compare_team = st.selectbox(
        "Compare against",
        [team for team in teams if team != selected_team],
        index=0,
        label_visibility="collapsed"
    )

    st.divider()

    st.caption(
        f"{len(matches)} matches · {len(teams)} teams"
    )

    st.caption(
        f"{matches['Date'].min():%d %b %Y} — "
        f"{matches['Date'].max():%d %b %Y}"
    )

summary = team_summary(matches, selected_team)
comparison = team_summary(matches, compare_team)
games = team_matches(matches, selected_team)
selected_rank = rankings.loc[rankings["Team"] == selected_team].iloc[0]

st.markdown(
    '<div class="eyebrow">UCLYTICS / TEAM SCOUT</div>',
    unsafe_allow_html=True
)

st.title(selected_team)

st.markdown(
    '<div class="lede">'
    'Performance, form and team strength analysis.'
    '</div>',
    unsafe_allow_html=True
)
stat_cols = st.columns(5)

main_stats = [
    ("MATCHES", summary["played"]),
    ("POINTS", summary["points"]),
    ("GOAL DIFFERENCE", f"{summary['goal_diff']:+d}"),
    ("UCLYTICS STRENGTH", f"{selected_rank['Strength index']}/100"),
    ("ELO RATING", f"{selected_rank['Elo']:.0f}")
]

for column, (label, value) in zip(stat_cols, main_stats):
    with column:
        st.metric(label, value)
st.markdown("## Team scout")

scout_cols = st.columns(6)

scout_stats = [
    ("RECORD", f"{summary['wins']}W {summary['draws']}D {summary['losses']}L"),
    ("GOALS / MATCH", f"{summary['goals_per_game']:.2f}"),
    ("CONCEDED / MATCH", f"{summary['conceded_per_game']:.2f}"),
    ("CLEAN SHEETS", summary["clean_sheets"]),
    ("HOME RECORD", summary["home_record"]),
    ("AWAY RECORD", summary["away_record"])
]

for column, (label, value) in zip(scout_cols, scout_stats):
    with column:
        st.metric(label, value)
# =========================================================
# RECENT FORM + PERFORMANCE
# =========================================================

left, right = st.columns([1.25, 1], gap="large")

with left:

    st.markdown("### Recent form")

    recent_results = games["Result"].tolist()[-8:]

    # Display W/D/L as simple coloured badges
    badges = ""

    for result in recent_results:

        if result == "W":
            bg = "#d9f36a"
            text = "#111111"

        elif result == "D":
            bg = "#747c7b"
            text = "#ffffff"

        else:
            bg = "#ff836d"
            text = "#111111"

        badges += f"""
        <span style="
            display:inline-flex;
            align-items:center;
            justify-content:center;
            width:32px;
            height:32px;
            border-radius:50%;
            background:{bg};
            color:{text};
            font-family:monospace;
            font-weight:600;
            font-size:13px;
            margin-right:6px;
        ">{result}</span>
        """

    st.markdown(
        badges,
        unsafe_allow_html=True
    )

    st.caption("Last 8 matches")

    # -----------------------------
    # GOALS CHART
    # -----------------------------

    chart_data = games[
        ["Date", "Goals For", "Goals Against"]
    ].tail(8).copy()

    chart_data.columns = [
        "Date",
        "Goals scored",
        "Goals conceded"
    ]

    fig = px.line(
        chart_data,
        x="Date",
        y=["Goals scored", "Goals conceded"],
        markers=True
    )

    fig.update_traces(line=dict(width=3))

    fig.update_layout(
        height=320,
        margin=dict(
            l=10,
            r=10,
            t=20,
            b=10
        ),
        paper_bgcolor="#151c1d",
        plot_bgcolor="#151c1d",
        font_color="#f5f5f0",
        legend_title=None
    )

    fig.update_xaxes(
        showgrid=False,
        title=None,
        tickfont=dict(
            color="#a5adaa"
        )
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor="#354041",
        title=None,
        tickfont=dict(
            color="#a5adaa"
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": False
        }
    )


with right:

    st.markdown("### Results breakdown")

    result_counts = (
        games["Result"]
        .value_counts()
        .reindex(
            ["W", "D", "L"],
            fill_value=0
        )
        .reset_index()
    )

    result_counts.columns = [
        "Result",
        "Matches"
    ]

    fig = px.bar(
        result_counts,
        x="Result",
        y="Matches",
        color="Result",
        text="Matches",
        color_discrete_map={
            "W": "#d9f36a",
            "D": "#747c7b",
            "L": "#ff836d"
        }
    )

    fig.update_layout(
        height=320,
        margin=dict(
            l=10,
            r=10,
            t=20,
            b=10
        ),
        paper_bgcolor="#151c1d",
        plot_bgcolor="#151c1d",
        font_color="#f5f5f0",
        showlegend=False
    )

    fig.update_xaxes(
        showgrid=False,
        title=None
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor="#354041",
        title=None
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": False
        }
    )

st.markdown("## Compare teams")
st.caption(
    f"{selected_team} vs {compare_team}"
)
metric_labels = ["Win rate", "Goals / match", "Points / match", "Clean-sheet %", "Strength index"]
def compare_value(team, metric):
    row = rankings.loc[rankings["Team"] == team].iloc[0]
    return {"Win rate": row["win_rate"], "Goals / match": row["goals_per_game"], "Points / match": row["points_per_game"], "Clean-sheet %": row["clean_sheets"] / row["played"] * 100, "Strength index": row["Strength index"]}[metric]
compare_data = pd.DataFrame([(metric, team, compare_value(team, metric)) for metric in metric_labels for team in [selected_team, compare_team]], columns=["Metric", "Team", "Value"])
fig = px.bar(
    compare_data,
    x="Metric",
    y="Value",
    color="Team",
    barmode="group",
    text_auto=".1f",
    color_discrete_sequence=["#d9f36a", "#ff836d"]
)

fig.update_layout(
    height=350,
    margin=dict(l=10, r=10, t=20, b=30),
    paper_bgcolor="#151c1d",
    plot_bgcolor="#151c1d",
    font_color="#f5f5f0",
    legend_title=None
)

fig.update_xaxes(
    showgrid=False,
    tickfont=dict(color="#d0d5d2")
)

fig.update_yaxes(
    showgrid=True,
    gridcolor="#354041",
    tickfont=dict(color="#a5adaa")
)

st.plotly_chart(
    fig,
    use_container_width=True,
    config={"displayModeBar": False}
)

with st.expander("Detailed comparison table"):
    detail = rankings[rankings["Team"].isin([selected_team, compare_team])][["Team", "played", "wins", "draws", "losses", "goals_for", "goals_against", "points", "Elo", "Strength index"]].copy()
    detail.columns = ["Team", "Played", "Wins", "Draws", "Losses", "For", "Against", "Points", "Elo", "Strength index"]
    st.dataframe(detail, hide_index=True, use_container_width=True)

st.markdown("## Power rankings")

st.caption(
    "Composite score combines Elo, points efficiency and "
    "goal difference. Elo is calculated chronologically "
    "from the supplied matches."
)
ranking_view = rankings[["Team", "Power score", "Elo", "Strength index", "played", "wins", "draws", "losses", "goals_for", "goals_against"]].copy()
ranking_view.insert(0, "Rank", range(1, len(ranking_view) + 1))
ranking_view.columns = ["Rank", "Team", "Power score", "Elo", "Strength index", "Played", "Wins", "Draws", "Losses", "Goals for", "Goals against"]
st.dataframe(
    ranking_view,
    hide_index=True,
    use_container_width=True,
    height=520
)

st.markdown("## Tournament simulator")

st.caption(
    "Test how the strongest teams perform across "
    "repeated simulated knockout tournaments."
)
sim_col, _ = st.columns([1, 2])
with sim_col:
    field_size = st.select_slider("Field size", options=[4, 8, 16], value=min(16, 2 ** int(np.floor(np.log2(len(teams))))))
    simulations = st.slider("Simulations", 500, 10000, 2000, step=500)
field = rankings.head(min(field_size, len(rankings)))["Team"].tolist()
if len(field) >= 2 and len(field) % 2 == 0:
    sim_result = simulate_tournament(field, matches, elos, simulations=simulations, neutral=True, seed=42)
    st.caption(
    f"Based on the top {len(field)} power-ranked teams. "
    "Neutral knockout matches use no home advantage."
)
    st.dataframe(sim_result, hide_index=True, use_container_width=True, column_config={"Champion probability": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=100), "Final probability": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=100)})
else:
    st.info("There are not enough teams for a tournament simulation.")

st.markdown("## Match log")
display_games = games[["Date", "Opponent", "Venue", "Score", "Result", "Goals For", "Goals Against"]].copy()
display_games["Date"] = display_games["Date"].dt.strftime("%d %b %Y")
display_games.columns = ["Date", "Opponent", "Venue", "Score", "Result", "For", "Against"]
st.dataframe(display_games, use_container_width=True, hide_index=True)
st.caption("Strength index is a directional 0–100 measure. Elo and probabilities are model outputs, not official UEFA ratings.")

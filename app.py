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


def team_matches(matches, team):
    home = matches[matches["Home Team"] == team].copy()
    home["Opponent"], home["Venue"] = home["Away Team"], "Home"
    home["Goals For"], home["Goals Against"] = home["Home Goals"], home["Away Goals"]
    away = matches[matches["Away Team"] == team].copy()
    away["Opponent"], away["Venue"] = away["Home Team"], "Away"
    away["Goals For"], away["Goals Against"] = away["Away Goals"], away["Home Goals"]
    games = pd.concat([home, away]).sort_values("Date").reset_index(drop=True)
    games["Result"] = np.select(
        [games["Goals For"] > games["Goals Against"], games["Goals For"] < games["Goals Against"]],
        ["W", "L"],
        default="D",
    )
    games["Points"] = games["Result"].map({"W": 3, "D": 1, "L": 0})
    games["Clean Sheet"] = games["Goals Against"].eq(0)
    games["BTTS"] = games["Goals For"].gt(0) & games["Goals Against"].gt(0)
    return games


def team_summary(matches, team):
    games = team_matches(matches, team)
    played = len(games)
    wins, draws, losses = [(games["Result"] == result).sum() for result in ["W", "D", "L"]]
    gf, ga = int(games["Goals For"].sum()), int(games["Goals Against"].sum())
    points = int(games["Points"].sum())
    return {
        "played": played, "wins": int(wins), "draws": int(draws), "losses": int(losses),
        "goals_for": gf, "goals_against": ga, "goal_diff": gf - ga, "points": points,
        "points_per_game": points / played if played else 0,
        "win_rate": wins / played * 100 if played else 0,
        "goals_per_game": gf / played if played else 0,
        "conceded_per_game": ga / played if played else 0,
        "clean_sheets": int(games["Clean Sheet"].sum()),
        "btts": int(games["BTTS"].sum()),
        "home_record": f"{(games[games['Venue'] == 'Home']['Result'] == 'W').sum()}W {(games[games['Venue'] == 'Home']['Result'] == 'D').sum()}D {(games[games['Venue'] == 'Home']['Result'] == 'L').sum()}L",
        "away_record": f"{(games[games['Venue'] == 'Away']['Result'] == 'W').sum()}W {(games[games['Venue'] == 'Away']['Result'] == 'D').sum()}D {(games[games['Venue'] == 'Away']['Result'] == 'L').sum()}L",
    }


def elo_ratings(matches, k_factor=24, home_advantage=55):
    teams = sorted(set(matches["Home Team"]).union(matches["Away Team"]))
    ratings = {team: 1500.0 for team in teams}
    history = []
    for _, match in matches.sort_values("Date").iterrows():
        home, away = match["Home Team"], match["Away Team"]
        before = dict(ratings)
        expected_home = 1 / (1 + 10 ** ((ratings[away] - (ratings[home] + home_advantage)) / 400))
        actual_home = 1 if match["Home Goals"] > match["Away Goals"] else 0 if match["Home Goals"] < match["Away Goals"] else 0.5
        margin = max(1.0, np.log1p(abs(match["Home Goals"] - match["Away Goals"])) * 2.2)
        change = k_factor * margin * (actual_home - expected_home)
        ratings[home] += change
        ratings[away] -= change
        history.append({"Date": match["Date"], "Home Team": home, "Away Team": away, "Home Elo": before[home], "Away Elo": before[away]})
    return ratings, pd.DataFrame(history)


def power_rankings(matches):
    ratings, _ = elo_ratings(matches)
    rows = []
    for team in sorted(ratings):
        summary = team_summary(matches, team)
        # Elo is the anchor; performance and goal difference make small samples legible.
        score = 0.65 * ratings[team] + 0.25 * (summary["points_per_game"] / 3 * 2000) + 0.10 * (1500 + summary["goal_diff"] * 18)
        rows.append({"Team": team, "Power score": round(score / 10, 1), "Elo": round(ratings[team]), **summary})
    return pd.DataFrame(rows).sort_values(["Power score", "Elo"], ascending=False).reset_index(drop=True)


def strength_index(row):
    # A transparent, capped index: results (40%), chance creation proxy (25%), defence (20%), Elo (15%).
    attack = min(row["goals_per_game"] / 3, 1)
    defence = max(0, 1 - row["conceded_per_game"] / 3)
    form = row["points_per_game"] / 3
    elo = np.clip((row["Elo"] - 1200) / 500, 0, 1)
    return round(100 * (0.40 * form + 0.25 * attack + 0.20 * defence + 0.15 * elo), 1)


def match_probability(team_a, team_b, ratings):
    difference = ratings[team_a] - ratings[team_b]
    win_a = 1 / (1 + 10 ** (-difference / 400))
    return float(np.clip(win_a, 0.08, 0.92))


def simulate_tournament(teams, ratings, simulations=2000):
    rng = np.random.default_rng(42)
    champions = {team: 0 for team in teams}
    finalist = {team: 0 for team in teams}
    for _ in range(simulations):
        field = list(teams)
        rng.shuffle(field)
        while len(field) > 1:
            winners = []
            for index in range(0, len(field), 2):
                a, b = field[index], field[index + 1]
                winners.append(a if rng.random() < match_probability(a, b, ratings) else b)
            if len(winners) == 2:
                finalist[winners[0]] += 1
                finalist[winners[1]] += 1
            field = winners
        champions[field[0]] += 1
    result = pd.DataFrame({"Team": list(champions), "Champion probability": [champions[t] / simulations * 100 for t in champions], "Final probability": [finalist[t] / simulations * 100 for t in champions]})
    return result.sort_values("Champion probability", ascending=False).reset_index(drop=True)


matches = load_matches()
teams = sorted(set(matches["Home Team"]).union(matches["Away Team"]))
rankings = power_rankings(matches)
rankings["Strength index"] = rankings.apply(strength_index, axis=1)
elos, elo_history = elo_ratings(matches)

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Space+Grotesk:wght@400;500;600;700&display=swap');
:root { --ink:#f3f0e8; --muted:#9b9c9b; --line:#2c3334; --lime:#d9f36a; --coral:#ff836d; }
.stApp { background:#101617; color:var(--ink); } [data-testid="stSidebar"] { background:#171d1d; border-right:1px solid var(--line); }
[data-testid="stSidebar"] *, h1,h2,h3,p,label,.stMarkdown { font-family:'Space Grotesk',sans-serif; }
h1 { font-size:3.5rem !important; line-height:1 !important; } h2 { font-size:1.35rem !important; }
.eyebrow { color:var(--lime); font-family:'DM Mono',monospace; font-size:.72rem; letter-spacing:.12em; text-transform:uppercase; }
.lede { color:var(--muted); font-size:1rem; } .record { font-family:'DM Mono',monospace; color:var(--muted); }
.record strong { color:var(--lime); font-size:1.15rem; } div[data-testid="stMetric"] { background:#171d1d; border:1px solid var(--line); padding:1rem; }
div[data-testid="stMetricLabel"] { color:var(--muted); } div[data-testid="stMetricValue"] { color:var(--ink); }
.block-container { max-width:1450px; padding-top:3rem; }
</style>""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<div class="eyebrow">UCLytics / 02</div>', unsafe_allow_html=True)
    st.markdown("## Team intelligence")
    selected_team = st.selectbox("Focus team", teams, index=teams.index("Real Madrid") if "Real Madrid" in teams else 0)
    compare_team = st.selectbox("Compare against", [team for team in teams if team != selected_team], index=0)
    st.divider()
    st.caption(f"{len(matches)} matches · {len(teams)} teams")
    st.caption(f"{matches['Date'].min():%d %b %Y} — {matches['Date'].max():%d %b %Y}")

summary = team_summary(matches, selected_team)
comparison = team_summary(matches, compare_team)
games = team_matches(matches, selected_team)
selected_rank = rankings.loc[rankings["Team"] == selected_team].iloc[0]

st.markdown('<div class="eyebrow">UEFA CHAMPIONS LEAGUE / TEAM INTELLIGENCE</div>', unsafe_allow_html=True)
st.title(selected_team)
st.markdown('<div class="lede">Performance profile, power ranking, scouting and scenario analysis.</div>', unsafe_allow_html=True)

stat_cols = st.columns(5)
for column, (label, value) in zip(stat_cols, [("Matches", summary["played"]), ("Points", summary["points"]), ("Goal difference", f"{summary['goal_diff']:+d}"), ("Strength index", f"{selected_rank['Strength index']}/100"), ("Elo rating", f"{selected_rank['Elo']:.0f}")]):
    with column:
        st.metric(label, value)

st.markdown("## Team scout")
scout_cols = st.columns(6)
for column, (label, value) in zip(scout_cols, [("Record", f"{summary['wins']}W {summary['draws']}D {summary['losses']}L"), ("Goals / match", f"{summary['goals_per_game']:.2f}"), ("Conceded / match", f"{summary['conceded_per_game']:.2f}"), ("Clean sheets", summary["clean_sheets"]), ("Home record", summary["home_record"]), ("Away record", summary["away_record"])]):
    with column:
        st.metric(label, value)

left, right = st.columns([1.2, 1], gap="large")
with left:
    form = "".join(games["Result"].tolist()[-8:])
    st.markdown(f'<div class="record">LAST 8 &nbsp; <strong>{form}</strong></div>', unsafe_allow_html=True)
    chart_data = games[["Date", "Goals For", "Goals Against"]].set_index("Date")
    chart_data.columns = ["Goals scored", "Goals conceded"]
    st.line_chart(chart_data, color=["#d9f36a", "#ff836d"], height=280)
with right:
    result_counts = games["Result"].value_counts().reindex(["W", "D", "L"], fill_value=0).reset_index()
    result_counts.columns = ["Result", "Matches"]
    fig = px.bar(result_counts, x="Result", y="Matches", color="Result", text="Matches", color_discrete_map={"W":"#d9f36a", "D":"#a9b1ad", "L":"#ff836d"})
    fig.update_layout(height=280, margin=dict(l=10,r=10,t=30,b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#f3f0e8", showlegend=False)
    fig.update_xaxes(showgrid=False, title=None); fig.update_yaxes(showgrid=True, gridcolor="#2c3334", title=None)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

st.markdown("## Compare teams")
metric_labels = ["Win rate", "Goals / match", "Points / match", "Clean-sheet %", "Strength index"]
def compare_value(team, metric):
    row = rankings.loc[rankings["Team"] == team].iloc[0]
    return {"Win rate": row["win_rate"], "Goals / match": row["goals_per_game"], "Points / match": row["points_per_game"], "Clean-sheet %": row["clean_sheets"] / row["played"] * 100, "Strength index": row["Strength index"]}[metric]
compare_data = pd.DataFrame([(metric, team, compare_value(team, metric)) for metric in metric_labels for team in [selected_team, compare_team]], columns=["Metric", "Team", "Value"])
fig = px.bar(compare_data, x="Metric", y="Value", color="Team", barmode="group", text_auto=".1f", color_discrete_sequence=["#d9f36a", "#ff836d"])
fig.update_layout(height=330, margin=dict(l=10,r=10,t=20,b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#f3f0e8", legend_title=None)
fig.update_xaxes(showgrid=False); fig.update_yaxes(showgrid=True, gridcolor="#2c3334")
st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with st.expander("Detailed comparison table"):
    detail = rankings[rankings["Team"].isin([selected_team, compare_team])][["Team", "played", "wins", "draws", "losses", "goals_for", "goals_against", "points", "Elo", "Strength index"]].copy()
    detail.columns = ["Team", "Played", "Wins", "Draws", "Losses", "For", "Against", "Points", "Elo", "Strength index"]
    st.dataframe(detail, hide_index=True, use_container_width=True)

st.markdown("## Power rankings")
st.caption("Composite score: 65% Elo, 25% points efficiency and 10% goal difference. Elo is calculated chronologically from the supplied matches.")
ranking_view = rankings[["Team", "Power score", "Elo", "Strength index", "played", "wins", "draws", "losses", "goals_for", "goals_against"]].copy()
ranking_view.insert(0, "Rank", range(1, len(ranking_view) + 1))
ranking_view.columns = ["Rank", "Team", "Power score", "Elo", "Strength index", "Played", "Wins", "Draws", "Losses", "Goals for", "Goals against"]
st.dataframe(ranking_view, hide_index=True, use_container_width=True)

st.markdown("## Tournament simulator")
sim_col, _ = st.columns([1, 2])
with sim_col:
    field_size = st.select_slider("Field size", options=[4, 8, 16], value=min(16, 2 ** int(np.floor(np.log2(len(teams))))))
    simulations = st.slider("Simulations", 500, 10000, 2000, step=500)
field = rankings.head(min(field_size, len(rankings)))["Team"].tolist()
if len(field) >= 2 and len(field) % 2 == 0:
    sim_result = simulate_tournament(field, elos, simulations)
    st.caption(f"Simulated knockout tournament using the top {len(field)} power-ranked teams. Home advantage is not applied to neutral knockout matches.")
    st.dataframe(sim_result, hide_index=True, use_container_width=True, column_config={"Champion probability": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=100), "Final probability": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=100)})
else:
    st.info("There are not enough teams for a tournament simulation.")

st.markdown("## Match log")
display_games = games[["Date", "Opponent", "Venue", "Score", "Result", "Goals For", "Goals Against"]].copy()
display_games["Date"] = display_games["Date"].dt.strftime("%d %b %Y")
display_games.columns = ["Date", "Opponent", "Venue", "Score", "Result", "For", "Against"]
st.dataframe(display_games, use_container_width=True, hide_index=True)
st.caption("Strength index is a directional 0–100 measure. Elo and probabilities are model outputs, not official UEFA ratings.")

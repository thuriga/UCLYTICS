import os

import pandas as pd
import plotly.express as px
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
	data["Date"] = pd.to_datetime(data["Date"])
	data["Score"] = data["Home Goals"].astype(str) + " - " + data["Away Goals"].astype(str)
	return data.sort_values("Date")


def team_matches(matches, team):
	home = matches[matches["Home Team"] == team].copy()
	home["Opponent"] = home["Away Team"]
	home["Venue"] = "Home"
	home["Goals For"] = home["Home Goals"]
	home["Goals Against"] = home["Away Goals"]
	away = matches[matches["Away Team"] == team].copy()
	away["Opponent"] = away["Home Team"]
	away["Venue"] = "Away"
	away["Goals For"] = away["Away Goals"]
	away["Goals Against"] = away["Home Goals"]
	games = pd.concat([home, away]).sort_values("Date")
	games["Result"] = games.apply(
		lambda row: "W" if row["Goals For"] > row["Goals Against"] else "L" if row["Goals For"] < row["Goals Against"] else "D",
		axis=1,
	)
	games["Points"] = games["Result"].map({"W": 3, "D": 1, "L": 0})
	return games


def team_summary(matches, team):
	games = team_matches(matches, team)
	wins = int((games["Result"] == "W").sum())
	draws = int((games["Result"] == "D").sum())
	losses = int((games["Result"] == "L").sum())
	played = len(games)
	goals_for = int(games["Goals For"].sum())
	goals_against = int(games["Goals Against"].sum())
	points = int(games["Points"].sum())
	win_rate = wins / played * 100 if played else 0
	strength = round((win_rate * 0.45) + ((goals_for / played) * 18) + (points / (played * 3) * 25), 1) if played else 0
	return {
		"played": played,
		"wins": wins,
		"draws": draws,
		"losses": losses,
		"goals_for": goals_for,
		"goals_against": goals_against,
		"goal_diff": goals_for - goals_against,
		"points": points,
		"win_rate": win_rate,
		"strength": strength,
	}


matches = load_matches()
teams = sorted(set(matches["Home Team"]).union(matches["Away Team"]))

st.markdown(
	"""
	<style>
	@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Space+Grotesk:wght@400;500;600;700&display=swap');
	:root { --ink: #f3f0e8; --muted: #9b9c9b; --line: #2c3334; --lime: #d9f36a; --coral: #ff836d; }
	.stApp { background: #101617; color: var(--ink); }
	[data-testid="stSidebar"] { background: #171d1d; border-right: 1px solid var(--line); }
	[data-testid="stSidebar"] * { font-family: 'Space Grotesk', sans-serif; }
	h1, h2, h3, p, label, .stMarkdown { font-family: 'Space Grotesk', sans-serif; }
	h1 { letter-spacing: 0; font-size: 3.5rem !important; line-height: 1 !important; }
	h2 { font-size: 1.35rem !important; margin-top: 1.7rem !important; }
	.eyebrow { color: var(--lime); font-family: 'DM Mono', monospace; font-size: .72rem; letter-spacing: .12em; text-transform: uppercase; }
	.lede { color: var(--muted); font-size: 1rem; margin-top: -.7rem; }
	.metric-card { border-top: 1px solid var(--line); padding: 1rem 0 .6rem; }
	.metric-label { color: var(--muted); font-family: 'DM Mono', monospace; font-size: .68rem; text-transform: uppercase; letter-spacing: .08em; }
	.metric-value { color: var(--ink); font-size: 2rem; font-weight: 600; margin-top: .2rem; }
	.metric-accent { color: var(--lime); }
	.record { font-family: 'DM Mono', monospace; font-size: .82rem; color: var(--muted); }
	.record strong { color: var(--lime); font-size: 1.15rem; }
	div[data-testid="stMetric"] { background: #171d1d; border: 1px solid var(--line); padding: 1rem; }
	div[data-testid="stMetricLabel"] { color: var(--muted); }
	div[data-testid="stMetricValue"] { color: var(--ink); }
	.block-container { max-width: 1450px; padding-top: 3rem; }
	</style>
	""",
	unsafe_allow_html=True,
)

with st.sidebar:
	st.markdown('<div class="eyebrow">UCLytics / 01</div>', unsafe_allow_html=True)
	st.markdown("## Team intelligence")
	st.caption("A compact read on Champions League form, scoring, and strength.")
	selected_team = st.selectbox("Focus team", teams, index=teams.index("Real Madrid") if "Real Madrid" in teams else 0)
	compare_team = st.selectbox("Compare against", [team for team in teams if team != selected_team], index=0)
	st.divider()
	st.markdown("**Dataset**")
	st.caption(f"{len(matches)} matches · {len(teams)} teams")
	st.caption(f"{matches['Date'].min():%d %b %Y} — {matches['Date'].max():%d %b %Y}")

summary = team_summary(matches, selected_team)
comparison = team_summary(matches, compare_team)
games = team_matches(matches, selected_team)

st.markdown('<div class="eyebrow">UEFA CHAMPIONS LEAGUE / TEAM INTELLIGENCE</div>', unsafe_allow_html=True)
st.title(selected_team)
st.markdown('<div class="lede">Performance profile built from the available match record.</div>', unsafe_allow_html=True)

stat_cols = st.columns(4)
stats = [("Matches", summary["played"]), ("Points", summary["points"]), ("Goal difference", f"{summary['goal_diff']:+d}"), ("Strength index", f"{summary['strength']}/100")]
for column, (label, value) in zip(stat_cols, stats):
	with column:
		st.metric(label, value)

st.markdown("## Form at a glance")
left, right = st.columns([1.2, 1], gap="large")
with left:
	form = "".join(games["Result"].tolist())
	st.markdown(f'<div class="record">LATEST FORM &nbsp; <strong>{form}</strong></div>', unsafe_allow_html=True)
	chart_data = games[["Date", "Goals For", "Goals Against"]].set_index("Date")
	chart_data.columns = ["Goals scored", "Goals conceded"]
	st.line_chart(chart_data, color=["#d9f36a", "#ff836d"], height=280)
with right:
	result_counts = games["Result"].value_counts().reindex(["W", "D", "L"], fill_value=0).reset_index()
	result_counts.columns = ["Result", "Matches"]
	fig = px.bar(result_counts, x="Result", y="Matches", color="Result", text="Matches", color_discrete_map={"W": "#d9f36a", "D": "#a9b1ad", "L": "#ff836d"})
	fig.update_layout(height=280, margin=dict(l=10, r=10, t=30, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#f3f0e8", showlegend=False)
	fig.update_xaxes(showgrid=False, title=None)
	fig.update_yaxes(showgrid=True, gridcolor="#2c3334", title=None)
	st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

st.markdown("## Team comparison")
compare_data = pd.DataFrame({"Metric": ["Win rate", "Goals scored / match", "Points / match", "Strength index"], selected_team: [summary["win_rate"], summary["goals_for"] / summary["played"], summary["points"] / summary["played"], summary["strength"]], compare_team: [comparison["win_rate"], comparison["goals_for"] / comparison["played"], comparison["points"] / comparison["played"], comparison["strength"]]}).melt("Metric", var_name="Team", value_name="Value")
fig = px.bar(compare_data, x="Metric", y="Value", color="Team", barmode="group", text_auto=".1f", color_discrete_sequence=["#d9f36a", "#ff836d"])
fig.update_layout(height=330, margin=dict(l=10, r=10, t=20, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#f3f0e8", legend_title=None)
fig.update_xaxes(showgrid=False)
fig.update_yaxes(showgrid=True, gridcolor="#2c3334")
st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

st.markdown("## Match log")
display_games = games[["Date", "Opponent", "Venue", "Score", "Result", "Goals For", "Goals Against"]].copy()
display_games["Date"] = display_games["Date"].dt.strftime("%d %b %Y")
display_games.columns = ["Date", "Opponent", "Venue", "Score", "Result", "For", "Against"]
st.dataframe(display_games, use_container_width=True, hide_index=True, column_config={"Result": st.column_config.TextColumn(width="small"), "Score": st.column_config.TextColumn(width="small")})

st.caption("Strength index blends win rate, scoring rate, and points efficiency. It is directional, not an official UEFA rating.")

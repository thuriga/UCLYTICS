import pandas as pd

from src.analytics import team_matches, team_summary, strength_index


def sample_matches():
    return pd.DataFrame([
        {"Date": "01/01/26", "Home Team": "A", "Away Team": "B", "Home Goals": 2, "Away Goals": 0},
        {"Date": "08/01/26", "Home Team": "B", "Away Team": "A", "Home Goals": 1, "Away Goals": 1},
    ]).assign(Date=lambda d: pd.to_datetime(d["Date"], dayfirst=True))


def test_team_matches_calculates_results_and_points():
    games = team_matches(sample_matches(), "A")
    assert games["Result"].tolist() == ["W", "D"]
    assert games["Points"].tolist() == [3, 1]
    assert games["Goals For"].tolist() == [2, 1]


def test_team_summary_calculates_core_metrics():
    summary = team_summary(sample_matches(), "A")
    assert summary["played"] == 2
    assert summary["wins"] == 1
    assert summary["draws"] == 1
    assert summary["points"] == 4
    assert summary["goals_for"] == 3
    assert summary["goal_diff"] == 2
    assert summary["win_rate"] == 50


def test_strength_index_stays_within_range():
    row = pd.Series({
        "goals_per_game": 2,
        "conceded_per_game": 1,
        "points_per_game": 2,
        "Elo": 1500,
    })
    assert 0 <= strength_index(row) <= 100

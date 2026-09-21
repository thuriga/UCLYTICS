import pandas as pd
import pytest

from src.models import elo_ratings, simulate_match, simulate_tournament


def sample_matches():
    return pd.DataFrame([
        {"Date": pd.Timestamp("2026-01-01"), "Home Team": "A", "Away Team": "B", "Home Goals": 2, "Away Goals": 0},
        {"Date": pd.Timestamp("2026-01-08"), "Home Team": "B", "Away Team": "A", "Home Goals": 1, "Away Goals": 1},
        {"Date": pd.Timestamp("2026-01-15"), "Home Team": "A", "Away Team": "C", "Home Goals": 1, "Away Goals": 0},
        {"Date": pd.Timestamp("2026-01-22"), "Home Team": "C", "Away Team": "B", "Home Goals": 0, "Away Goals": 2},
    ])


def test_elo_is_deterministic():
    ratings, history = elo_ratings(sample_matches())
    assert ratings["A"] > ratings["B"]
    assert len(history) == 4


def test_match_simulation_probabilities_sum_to_about_100():
    ratings, _ = elo_ratings(sample_matches())
    result = simulate_match("A", "B", sample_matches(), ratings, simulations=2000)
    total = result["team_a_win"] + result["draw"] + result["team_b_win"]
    assert total == pytest.approx(100, abs=1e-9)


def test_tournament_requires_power_of_two():
    ratings, _ = elo_ratings(sample_matches())
    with pytest.raises(ValueError):
        simulate_tournament(["A", "B", "C"], sample_matches(), ratings)


def test_tournament_probabilities_sum_to_100():
    ratings, _ = elo_ratings(sample_matches())
    result = simulate_tournament(["A", "B", "C", "D"], sample_matches(), ratings, simulations=200)
    assert result["Champion probability"].sum() == pytest.approx(100, abs=1e-9)

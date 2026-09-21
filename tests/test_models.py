import pandas as pd
import pytest

from src.models import elo_ratings
from src.simulation import simulate_match, simulate_tournament


def sample_matches():
    return pd.DataFrame([
        {"Date": pd.Timestamp("2026-01-01"), "Home Team": "A", "Away Team": "B", "Home Goals": 2, "Away Goals": 0},
        {"Date": pd.Timestamp("2026-01-08"), "Home Team": "B", "Away Team": "A", "Home Goals": 1, "Away Goals": 1},
        {"Date": pd.Timestamp("2026-01-15"), "Home Team": "A", "Away Team": "C", "Home Goals": 1, "Away Goals": 0},
        {"Date": pd.Timestamp("2026-01-22"), "Home Team": "C", "Away Team": "B", "Home Goals": 0, "Away Goals": 2},
        {"Date": pd.Timestamp("2026-01-29"), "Home Team": "C", "Away Team": "D", "Home Goals": 1, "Away Goals": 1},
        {"Date": pd.Timestamp("2026-02-05"), "Home Team": "D", "Away Team": "A", "Home Goals": 0, "Away Goals": 2},
    ])


def test_elo_is_deterministic():
    ratings, history = elo_ratings(sample_matches())
    assert ratings["A"] > ratings["B"]
    assert len(history) == 6


def test_match_simulation_probabilities_sum_to_100():
    matches = sample_matches()
    ratings, _ = elo_ratings(matches)
    result = simulate_match("A", "B", matches, ratings, simulations=2000)
    total = result["team_a_win"] + result["draw"] + result["team_b_win"]
    assert total == pytest.approx(100, abs=1e-9)
    assert result["a_rate"] > 0
    assert result["b_rate"] > 0


def test_tournament_requires_power_of_two():
    matches = sample_matches()
    ratings, _ = elo_ratings(matches)
    with pytest.raises(ValueError):
        simulate_tournament(["A", "B", "C"], matches, ratings)


def test_tournament_probabilities_sum_to_100():
    matches = sample_matches()
    ratings, _ = elo_ratings(matches)
    result = simulate_tournament(
        ["A", "B", "C", "D"], matches, ratings, simulations=500
    )
    assert result["Champion probability"].sum() == pytest.approx(100, abs=1e-9)
    assert result["Final probability"].sum() == pytest.approx(200, abs=1e-9)
    assert (result["Champion probability"] > 0).any()


def test_tournament_is_reproducible_with_seed():
    matches = sample_matches()
    ratings, _ = elo_ratings(matches)
    first = simulate_tournament(
        ["A", "B", "C", "D"], matches, ratings, simulations=200, seed=7
    )
    second = simulate_tournament(
        ["A", "B", "C", "D"], matches, ratings, simulations=200, seed=7
    )
    pd.testing.assert_frame_equal(first, second)


def test_simulation_rejects_duplicate_teams():
    matches = sample_matches()
    ratings, _ = elo_ratings(matches)
    with pytest.raises(ValueError):
        simulate_tournament(["A", "A"], matches, ratings)

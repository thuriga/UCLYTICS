import numpy as np
import pandas as pd


def poisson_rates(team_a, team_b, matches, ratings, neutral=True):
    """Estimate expected goals for a matchup from attack, defence and Elo."""
    team_rates = []

    for team in [team_a, team_b]:
        games = matches[
            (matches["Home Team"] == team) | (matches["Away Team"] == team)
        ]
        goals_for = (
            games.loc[games["Home Team"] == team, "Home Goals"].sum()
            + games.loc[games["Away Team"] == team, "Away Goals"].sum()
        )
        goals_against = (
            games.loc[games["Home Team"] == team, "Away Goals"].sum()
            + games.loc[games["Away Team"] == team, "Home Goals"].sum()
        )
        played = len(games)
        team_rates.append((
            float(goals_for / played) if played else 1.2,
            float(goals_against / played) if played else 1.2,
        ))

    (a_for, a_against), (b_for, b_against) = team_rates
    league_goals = (
        matches["Home Goals"].sum() + matches["Away Goals"].sum()
    ) / max(2 * len(matches), 1)
    base = max(float(league_goals), 0.5)

    elo_gap = (ratings[team_a] - ratings[team_b]) / 400
    a_rate = base * 0.5 * (a_for / base + b_against / base)
    b_rate = base * 0.5 * (b_for / base + a_against / base)

    # Elo provides a small adjustment rather than replacing the goal model.
    a_rate *= 10 ** (elo_gap * 0.10)
    b_rate *= 10 ** (-elo_gap * 0.10)

    if not neutral:
        a_rate *= 1.10
        b_rate *= 0.95

    return max(0.15, min(a_rate, 4.5)), max(0.15, min(b_rate, 4.5))


def _elo_tiebreak_winner(team_a, team_b, ratings, rng):
    """Approximate extra-time/penalty winner from Elo strength."""
    probability_a = 1 / (1 + 10 ** ((ratings[team_b] - ratings[team_a]) / 400))
    return team_a if rng.random() < probability_a else team_b


def simulate_match(
    team_a, team_b, matches, ratings, simulations=1000, neutral=True, seed=42
):
    """Simulate a single matchup by sampling Poisson-distributed goals."""
    if simulations <= 0:
        raise ValueError("simulations must be positive.")
    if team_a == team_b:
        raise ValueError("team_a and team_b must be different.")

    rng = np.random.default_rng(seed)
    a_rate, b_rate = poisson_rates(team_a, team_b, matches, ratings, neutral)

    a_goals = rng.poisson(a_rate, simulations)
    b_goals = rng.poisson(b_rate, simulations)

    return {
        "team_a": team_a,
        "team_b": team_b,
        "a_rate": a_rate,
        "b_rate": b_rate,
        "team_a_win": float((a_goals > b_goals).mean() * 100),
        "draw": float((a_goals == b_goals).mean() * 100),
        "team_b_win": float((a_goals < b_goals).mean() * 100),
        "most_common_score": pd.Series(
            list(zip(a_goals, b_goals))
        ).value_counts().index[0],
    }


def simulate_tournament(
    teams, matches, ratings, simulations=2000, neutral=True, seed=42
):
    """Simulate a knockout tournament and return champion/final frequencies."""
    if len(teams) < 2 or len(teams) & (len(teams) - 1):
        raise ValueError("Number of teams must be a power of two and at least 2.")
    if simulations <= 0:
        raise ValueError("simulations must be positive.")
    if len(set(teams)) != len(teams):
        raise ValueError("teams must contain unique team names.")
    missing_ratings = set(teams) - set(ratings)
    if missing_ratings:
        raise ValueError(f"Missing Elo ratings for: {sorted(missing_ratings)}")

    rng = np.random.default_rng(seed)
    champions = {team: 0 for team in teams}
    finalists = {team: 0 for team in teams}

    # Precompute matchup rates once. The same teams can meet many times
    # across simulations, so recalculating them inside every match is wasteful.
    matchup_rates = {}
    for index, team_a in enumerate(teams):
        for team_b in teams[index + 1:]:
            matchup_rates[(team_a, team_b)] = poisson_rates(
                team_a, team_b, matches, ratings, neutral
            )

    def get_rates(team_a, team_b):
        if (team_a, team_b) in matchup_rates:
            return matchup_rates[(team_a, team_b)]
        return matchup_rates[(team_b, team_a)][::-1]

    # Fully vectorized Monte Carlo across all simulations.
    # Each row of the field array represents one simulated tournament.
    team_list = list(teams)
    team_index = {team: i for i, team in enumerate(team_list)}
    n = len(team_list)

    rate_a = np.zeros((n, n), dtype=float)
    rate_b = np.zeros((n, n), dtype=float)
    for i, team_a in enumerate(team_list):
        for j, team_b in enumerate(team_list):
            if i == j:
                continue
            a_rate, b_rate = get_rates(team_a, team_b)
            rate_a[i, j] = a_rate
            rate_b[i, j] = b_rate

    elo_array = np.array([ratings[team] for team in team_list], dtype=float)
    fields = np.tile(np.arange(n), (simulations, 1))

    # Shuffle each simulated bracket independently.
    for row in fields:
        rng.shuffle(row)

    while fields.shape[1] > 1:
        a = fields[:, 0::2]
        b = fields[:, 1::2]
        a_rates = rate_a[a, b]
        b_rates = rate_b[a, b]

        a_goals = rng.poisson(a_rates)
        b_goals = rng.poisson(b_rates)

        a_wins = a_goals > b_goals
        b_wins = a_goals < b_goals
        ties = ~(a_wins | b_wins)

        winners = np.where(a_wins, a, b).astype(int)

        if np.any(ties):
            a_elo = elo_array[a[ties]]
            b_elo = elo_array[b[ties]]
            p_a = 1 / (1 + 10 ** ((b_elo - a_elo) / 400))
            winners[ties] = np.where(rng.random(np.count_nonzero(ties)) < p_a, a[ties], b[ties])

        if winners.shape[1] == 2:
            finalist_ids = winners
            finalists.update({team: 0 for team in []})
            for team_id, count in zip(*np.unique(finalist_ids, return_counts=True)):
                finalists[team_list[int(team_id)]] += int(count)

        fields = winners

    champion_ids, champion_counts = np.unique(fields[:, 0], return_counts=True)
    for team_id, count in zip(champion_ids, champion_counts):
        champions[team_list[int(team_id)]] += int(count)

    result = pd.DataFrame({
        "Team": list(teams),
        "Champion probability": [
            champions[team] / simulations * 100 for team in teams
        ],
        "Final probability": [
            finalists[team] / simulations * 100 for team in teams
        ],
    })

    return result.sort_values(
        "Champion probability", ascending=False
    ).reset_index(drop=True)

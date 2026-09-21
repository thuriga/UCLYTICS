import numpy as np
import pandas as pd


def elo_ratings(matches, k_factor=24, home_advantage=55):
    """Calculate chronological Elo ratings from match results."""
    teams = sorted(set(matches["Home Team"]).union(matches["Away Team"]))
    ratings = {team: 1500.0 for team in teams}
    history = []

    for _, match in matches.sort_values("Date").iterrows():
        home, away = match["Home Team"], match["Away Team"]
        before = dict(ratings)
        expected_home = 1 / (1 + 10 ** ((ratings[away] - (ratings[home] + home_advantage)) / 400))
        actual_home = (
            1 if match["Home Goals"] > match["Away Goals"]
            else 0 if match["Home Goals"] < match["Away Goals"]
            else 0.5
        )
        margin = max(1.0, np.log1p(abs(match["Home Goals"] - match["Away Goals"])) * 2.2)
        change = k_factor * margin * (actual_home - expected_home)
        ratings[home] += change
        ratings[away] -= change
        history.append({
            "Date": match["Date"],
            "Home Team": home,
            "Away Team": away,
            "Home Elo": before[home],
            "Away Elo": before[away],
        })

    return ratings, pd.DataFrame(history)


def power_rankings(matches):
    ratings, _ = elo_ratings(matches)
    rows = []
    for team in sorted(ratings):
        games = matches[(matches["Home Team"] == team) | (matches["Away Team"] == team)]
        played = len(games)
        goals_for = int(sum(
            games.loc[games["Home Team"] == team, "Home Goals"].sum()
            + games.loc[games["Away Team"] == team, "Away Goals"].sum()
        ))
        goals_against = int(
            games.loc[games["Home Team"] == team, "Away Goals"].sum()
            + games.loc[games["Away Team"] == team, "Home Goals"].sum()
        )
        points = 0
        for _, match in games.iterrows():
            gf = match["Home Goals"] if match["Home Team"] == team else match["Away Goals"]
            ga = match["Away Goals"] if match["Home Team"] == team else match["Home Goals"]
            points += 3 if gf > ga else 1 if gf == ga else 0
        ppg = points / played if played else 0
        gd = goals_for - goals_against
        score = 0.65 * ratings[team] + 0.25 * (ppg / 3 * 2000) + 0.10 * (1500 + gd * 18)
        rows.append({
            "Team": team, "Power score": round(score / 10, 1),
            "Elo": round(ratings[team]), "played": played,
            "points_per_game": ppg, "win_rate": sum(
                1 for _, m in games.iterrows()
                if (m["Home Goals"] > m["Away Goals"] and m["Home Team"] == team)
                or (m["Away Goals"] > m["Home Goals"] and m["Away Team"] == team)
            ) / played * 100 if played else 0,
            "goals_for": goals_for, "goals_against": goals_against,
            "goal_diff": gd,
        })

    result = pd.DataFrame(rows).sort_values(["Power score", "Elo"], ascending=False).reset_index(drop=True)
    return result


def _poisson_rates(team_a, team_b, matches, ratings, neutral=True):
    """Estimate expected goals using attack/defence rates with a small Elo adjustment."""
    team_games = []
    for team in [team_a, team_b]:
        games = matches[(matches["Home Team"] == team) | (matches["Away Team"] == team)]
        gf = sum(games.loc[games["Home Team"] == team, "Home Goals"]) + sum(games.loc[games["Away Team"] == team, "Away Goals"])
        ga = sum(games.loc[games["Home Team"] == team, "Away Goals"]) + sum(games.loc[games["Away Team"] == team, "Home Goals"])
        n = len(games)
        team_games.append((gf / n if n else 1.2, ga / n if n else 1.2))

    (a_for, a_against), (b_for, b_against) = team_games
    league_goals = (matches["Home Goals"].sum() + matches["Away Goals"].sum()) / max(2 * len(matches), 1)
    base = max(float(league_goals), 0.5)
    elo_gap = (ratings[team_a] - ratings[team_b]) / 400
    a_rate = base * 0.5 * (a_for / base + b_against / base) * 10 ** (elo_gap * 0.10)
    b_rate = base * 0.5 * (b_for / base + a_against / base) * 10 ** (-elo_gap * 0.10)
    if not neutral:
        a_rate *= 1.10
        b_rate *= 0.95
    return max(0.15, min(a_rate, 4.5)), max(0.15, min(b_rate, 4.5))


def simulate_match(team_a, team_b, matches, ratings, simulations=1000, neutral=True, seed=42):
    """Simulate a matchup by sampling Poisson-distributed goals."""
    rng = np.random.default_rng(seed)
    a_rate, b_rate = _poisson_rates(team_a, team_b, matches, ratings, neutral)
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
        "most_common_score": pd.Series(zip(a_goals, b_goals)).value_counts().index[0],
    }


def simulate_tournament(teams, matches, ratings, simulations=2000, neutral=True, seed=42):
    """Simulate knockout tournaments using Poisson-distributed match scores."""
    if len(teams) < 2 or len(teams) & (len(teams) - 1):
        raise ValueError("Number of teams must be a power of two and at least 2.")

    rng = np.random.default_rng(seed)
    champions = {team: 0 for team in teams}
    finalists = {team: 0 for team in teams}

    for _ in range(simulations):
        field = list(teams)
        rng.shuffle(field)
        while len(field) > 1:
            winners = []
            for index in range(0, len(field), 2):
                a, b = field[index], field[index + 1]
                a_rate, b_rate = _poisson_rates(a, b, matches, ratings, neutral)
                a_goals = rng.poisson(a_rate)
                b_goals = rng.poisson(b_rate)
                if a_goals == b_goals:
                    # Extra-time/penalty winner is approximated by Elo strength.
                    p_a = 1 / (1 + 10 ** ((ratings[b] - ratings[a]) / 400))
                    winner = a if rng.random() < p_a else b
                else:
                    winner = a if a_goals > b_goals else b
                winners.append(winner)
            if len(winners) == 2:
                finalists[winners[0]] += 1
                finalists[winners[1]] += 1
            field = winners

    return pd.DataFrame({
        "Team": list(champions),
        "Champion probability": [champions[t] / simulations * 100 for t in champions],
        "Final probability": [finalists[t] / simulations * 100 for t in champions],
    }).sort_values("Champion probability", ascending=False).reset_index(drop=True)

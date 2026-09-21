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

        expected_home = 1 / (
            1 + 10 ** ((ratings[away] - (ratings[home] + home_advantage)) / 400)
        )
        actual_home = (
            1
            if match["Home Goals"] > match["Away Goals"]
            else 0
            if match["Home Goals"] < match["Away Goals"]
            else 0.5
        )

        margin = max(
            1.0,
            np.log1p(abs(match["Home Goals"] - match["Away Goals"])) * 2.2,
        )
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
    """Build a transparent exploratory ranking from Elo, points and goal difference."""
    ratings, _ = elo_ratings(matches)
    rows = []

    for team in sorted(ratings):
        games = matches[
            (matches["Home Team"] == team) | (matches["Away Team"] == team)
        ]
        played = len(games)

        goals_for = int(
            games.loc[games["Home Team"] == team, "Home Goals"].sum()
            + games.loc[games["Away Team"] == team, "Away Goals"].sum()
        )
        goals_against = int(
            games.loc[games["Home Team"] == team, "Away Goals"].sum()
            + games.loc[games["Away Team"] == team, "Home Goals"].sum()
        )

        points = 0
        wins = 0
        for _, match in games.iterrows():
            gf = (
                match["Home Goals"]
                if match["Home Team"] == team
                else match["Away Goals"]
            )
            ga = (
                match["Away Goals"]
                if match["Home Team"] == team
                else match["Home Goals"]
            )
            if gf > ga:
                points += 3
                wins += 1
            elif gf == ga:
                points += 1

        ppg = points / played if played else 0
        goal_diff = goals_for - goals_against
        score = (
            0.65 * ratings[team]
            + 0.25 * (ppg / 3 * 2000)
            + 0.10 * (1500 + goal_diff * 18)
        )

        rows.append({
            "Team": team,
            "Power score": round(score / 10, 1),
            "Elo": round(ratings[team]),
            "played": played,
            "points_per_game": ppg,
            "win_rate": wins / played * 100 if played else 0,
            "goals_for": goals_for,
            "goals_against": goals_against,
            "goal_diff": goal_diff,
            "wins": wins,
            "draws": sum(
                1
                for _, match in games.iterrows()
                if (
                    match["Home Goals"] == match["Away Goals"]
                )
            ),
            "losses": (
                played
                - wins
                - sum(
                    1
                    for _, match in games.iterrows()
                    if match["Home Goals"] == match["Away Goals"]
                )
            ),
            "points": points,
        })

    return pd.DataFrame(rows).sort_values(
        ["Power score", "Elo"], ascending=False
    ).reset_index(drop=True)

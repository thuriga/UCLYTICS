import numpy as np
import pandas as pd


def team_matches(matches, team):
    """Return match-level statistics from one team's perspective."""
    home = matches[matches["Home Team"] == team].copy()
    home["Opponent"], home["Venue"] = home["Away Team"], "Home"
    home["Goals For"], home["Goals Against"] = home["Home Goals"], home["Away Goals"]

    away = matches[matches["Away Team"] == team].copy()
    away["Opponent"], away["Venue"] = away["Home Team"], "Away"
    away["Goals For"], away["Goals Against"] = away["Away Goals"], away["Home Goals"]

    games = pd.concat([home, away]).sort_values("Date").reset_index(drop=True)
    games["Result"] = np.select(
        [games["Goals For"] > games["Goals Against"],
         games["Goals For"] < games["Goals Against"]],
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
    wins = int((games["Result"] == "W").sum())
    draws = int((games["Result"] == "D").sum())
    losses = int((games["Result"] == "L").sum())
    gf = int(games["Goals For"].sum())
    ga = int(games["Goals Against"].sum())
    points = int(games["Points"].sum())

    home = games[games["Venue"] == "Home"]
    away = games[games["Venue"] == "Away"]

    return {
        "played": played,
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "goals_for": gf,
        "goals_against": ga,
        "goal_diff": gf - ga,
        "points": points,
        "points_per_game": points / played if played else 0,
        "win_rate": wins / played * 100 if played else 0,
        "goals_per_game": gf / played if played else 0,
        "conceded_per_game": ga / played if played else 0,
        "clean_sheets": int(games["Clean Sheet"].sum()),
        "btts": int(games["BTTS"].sum()),
        "home_record": f"{(home['Result'] == 'W').sum()}W {(home['Result'] == 'D').sum()}D {(home['Result'] == 'L').sum()}L",
        "away_record": f"{(away['Result'] == 'W').sum()}W {(away['Result'] == 'D').sum()}D {(away['Result'] == 'L').sum()}L",
    }


def strength_index(row):
    """Transparent 0-100 composite indicator."""
    attack = min(row["goals_per_game"] / 3, 1)
    defence = max(0, 1 - row["conceded_per_game"] / 3)
    form = row["points_per_game"] / 3
    elo = np.clip((row["Elo"] - 1200) / 500, 0, 1)
    return round(100 * (0.40 * form + 0.25 * attack + 0.20 * defence + 0.15 * elo), 1)

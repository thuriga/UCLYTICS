# UCLytics

### Champions League Team Intelligence Platform

UCLytics is an interactive football analytics application built with **Python, Pandas, NumPy, Plotly and Streamlit**.

It turns match results into an exploratory product for understanding team performance, comparing clubs, inspecting form and testing simulated knockout scenarios.

> **Project goal:** turn raw football match data into a clear, interactive analytical experience.

## What it does

### Team Scout
For a selected club, UCLytics calculates:
- Wins, draws and losses
- Points and points per game
- Goals scored and conceded
- Goal difference
- Clean sheets and BTTS
- Home and away records
- Recent form

### Elo ratings
Every team starts at **1500 Elo**. Ratings are updated chronologically after each match using:
- Expected result
- Actual result
- Home advantage
- A goal-margin adjustment

This creates a lightweight rating system that updates as new matches are added.

### Strength Index
The 0–100 UCLytics Strength Index is a transparent composite indicator:

| Component | Weight |
|---|---:|
| Points efficiency | 40% |
| Goals per game | 25% |
| Defensive performance | 20% |
| Elo | 15% |

The index is an analytical measure, not an official UEFA rating.

### Power Rankings
Power Rankings combine Elo, points efficiency and goal difference into a single exploratory score. The ranking is intended to make the underlying match data easier to compare rather than represent an official competition ranking.

### Team comparison
Two clubs can be compared across:
- Win rate
- Goals per match
- Points per match
- Clean-sheet rate
- Strength Index

### Tournament simulation
The tournament simulator now uses **Poisson-distributed goals** rather than selecting winners directly from Elo.

For each simulated match:
1. Attack and defensive scoring rates are estimated from the available match data.
2. A small Elo adjustment incorporates relative team strength.
3. Expected goals are sampled from Poisson distributions.
4. Draws are resolved using an Elo-based approximation for extra time/penalties.
5. The process is repeated across thousands of knockout tournaments.

The app reports simulated **champion** and **final** frequencies.

Because the current dataset is limited, these simulations should be treated as an exploration of the model rather than forecasts of real-world tournament outcomes.

## Project architecture

The application has been refactored so that the Streamlit interface is separated from the analytical logic:

```text
UCLYTICS/
├── app.py
├── data.csv
├── src/
│   ├── __init__.py
│   ├── data.py
│   ├── analytics.py
│   └── models.py
├── tests/
│   ├── test_analytics.py
│   └── test_models.py
├── requirements.txt
└── README.md
```

### Why the refactor?

Previously, data loading, team statistics, Elo calculations and simulation logic lived inside `app.py`.

The refactor separates these responsibilities:
- `src/data.py` — data loading and cleaning
- `src/analytics.py` — team-level metrics and Strength Index
- `src/models.py` — Elo, Power Rankings and simulation
- `app.py` — Streamlit presentation layer
- `tests/` — automated checks for the analytical logic

This makes the project easier to test, maintain and extend.

## Testing

The project includes unit tests for:
- Match-level result and points calculations
- Team summary metrics
- Strength Index bounds
- Deterministic Elo calculations
- Match simulation probability totals
- Tournament input validation
- Tournament probability totals

Run:

```bash
pip install -r requirements.txt
pytest
```

## Run locally

Clone the repository and install dependencies:

```bash
git clone https://github.com/thuriga/UCLYTICS.git
cd UCLYTICS
pip install -r requirements.txt
```

Start the Streamlit application:

```bash
streamlit run app.py
```

## Tech stack

- **Python** — application and modelling
- **Pandas** — data preparation and analysis
- **NumPy** — numerical calculations and simulation
- **Plotly** — interactive visualisation
- **Streamlit** — web application interface
- **Pytest** — automated testing

## Data and limitations

The application operates on the match data included in `data.csv`.

The current dataset is intentionally treated as a project dataset rather than a complete historical database. Results, ratings and simulation outputs are therefore sensitive to:
- Dataset coverage
- Sample size
- Team strength assumptions
- The Elo parameters
- The Poisson rate estimation method

The model does not include player availability, injuries, line-ups, transfers, tactical changes or other information that can affect real matches.

## What I learned

This project was built to explore the full path from **data → model → product**.

Key technical areas include:
- Cleaning inconsistent CSV data
- Designing reusable Python functions
- Building a chronological Elo rating system
- Combining multiple metrics into a transparent index
- Simulating outcomes with probability distributions
- Building interactive visualisations
- Separating application code from analytical logic
- Writing automated tests for data and modelling functions

## Future improvements

- Add a reproducible data-ingestion pipeline
- Expand and validate the match dataset
- Add interactive match-level exploration
- Improve expected-goals estimation
- Add confidence/uncertainty information to model outputs
- Add player-level analytics
- Deploy the application publicly

## Disclaimer

UCLytics is an independent data-analysis project.

Its ratings, rankings and simulations are model outputs for exploration and should not be interpreted as official UEFA ratings or predictions of actual tournament results.

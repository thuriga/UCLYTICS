# UCLytics

### Champions League Team Intelligence Platform

UCLytics turns football match data into an interactive analytical product using **Python, Pandas, NumPy, Plotly and Streamlit**.

> **Project goal:** explore the full path from raw data → model → usable product.

## Features

- **Team Scout** — results, goals, points, clean sheets, home/away records and recent form.
- **Elo ratings** — chronological 1500-base Elo with home advantage and goal-margin adjustment.
- **Strength Index** — transparent 0–100 composite using points efficiency, attack, defence and Elo.
- **Power Rankings** — exploratory score combining Elo, points efficiency and goal difference.
- **Team comparison** — compare win rate, goals per match, points per match, clean-sheet rate and Strength Index.
- **Tournament simulation** — Poisson goal simulation with a small Elo adjustment and seeded reproducibility.

## Tournament simulation

The simulator models each knockout match in two stages:

1. Estimate expected goals from each team's attack and defensive rates.
2. Apply a small Elo adjustment to those rates.
3. Sample goals from Poisson distributions.
4. If the sampled score is tied, use an Elo-based tiebreak to approximate extra time/penalties.
5. Repeat the bracket thousands of times and report champion/final frequencies.

This is an exploratory model, not a forecast. It does not include injuries, line-ups, transfers, tactics or other external information.

## Architecture

```text
UCLYTICS/
├── app.py
├── data.csv
├── src/
│   ├── __init__.py
│   ├── data.py
│   ├── analytics.py
│   ├── models.py
│   └── simulation.py
├── tests/
│   ├── test_analytics.py
│   ├── test_models.py
│   └── test_simulation.py
├── requirements.txt
└── README.md
```

### Separation of responsibilities

- `src/data.py` — loading, cleaning and validation
- `src/analytics.py` — team-level metrics and Strength Index
- `src/models.py` — Elo ratings and Power Rankings
- `src/simulation.py` — Poisson match and tournament simulation
- `app.py` — Streamlit presentation layer
- `tests/` — automated checks for the analytical and modelling logic

The refactor keeps the UI layer thin and makes the core logic reusable and testable.

## Data source

The bundled `data.csv` contains all 189 matches from the 2025/26 UEFA Champions League competition proper, covering the 36-team league phase, knockout play-offs and knockout phase. Results were sourced from OpenFootball's public-domain 2025/26 Champions League dataset and checked against UEFA's season statistics, which report 189 matches and 655 goals.

## Testing

The test suite covers:

- Match-level results and points
- Team summary metrics
- Strength Index bounds
- Deterministic Elo calculations
- Simulation probability totals
- Tournament input validation
- Seeded reproducibility
- Non-zero champion probabilities

Run:

```bash
pip install -r requirements.txt
pytest
```

## Run locally

```bash
git clone https://github.com/thuriga/UCLYTICS.git
cd UCLYTICS
pip install -r requirements.txt
streamlit run app.py
```

## Tech stack

| Tool | Purpose |
|---|---|
| Python | Application and modelling |
| Pandas | Data preparation and analysis |
| NumPy | Numerical calculations and simulation |
| Plotly | Interactive visualisation |
| Streamlit | Web application interface |
| Pytest | Automated testing |

## Data and limitations

The application operates on the match data included in `data.csv`. The dataset is a project dataset rather than a complete historical database, so outputs are sensitive to sample size, dataset coverage, Elo parameters and goal-rate assumptions.

The model does not include player availability, injuries, line-ups, transfers, tactical changes or other information that can affect real matches.

## What I learned

This project was built around **data → model → product**. It gave me practice with:

- Cleaning inconsistent CSV data
- Designing reusable Python functions
- Building a chronological Elo rating system
- Combining multiple metrics into a transparent index
- Simulating outcomes with probability distributions
- Building interactive visualisations
- Separating application code from analytical logic
- Writing automated tests

## Future improvements

- Build a reproducible data-ingestion pipeline
- Expand and validate the match dataset
- Add interactive match-level exploration
- Improve expected-goals estimation
- Add uncertainty information to model outputs
- Add player-level analytics
- Deploy the application publicly

## Disclaimer

UCLytics is an independent data-analysis project. Its ratings, rankings and simulations are model outputs for exploration and should not be interpreted as official UEFA ratings or predictions of actual tournament results.

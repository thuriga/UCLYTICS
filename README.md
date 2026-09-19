# UCLYTICS
# ⚽ UCLytics

### Champions League Football Intelligence Platform

UCLytics is an interactive football analytics platform that transforms UEFA Champions League match data into team intelligence, power rankings, team comparisons and tournament simulations.

The goal is to make football data easier to explore while experimenting with statistical modelling and product design.

---

## 🚀 Features

### 📊 Dashboard

Get an overview of the Champions League dataset including matches, teams and goals.

### 🏆 Power Rankings

Rank teams using a combination of:

* Elo rating
* Win rate
* Points efficiency
* Goals scored
* Goals conceded
* Goal difference

### 🔍 Team Scout

Explore an individual team's:

* Strength score
* Elo rating
* Win rate
* Attacking performance
* Defensive performance
* Recent form
* Match history

### ⚔️ Team Comparison

Compare two teams across key performance metrics.

### 🎲 Tournament Simulator

Run thousands of simulated 8-team knockout tournaments using:

* Elo ratings
* Expected scoring rates
* Poisson-distributed goals

The simulator produces estimated championship frequencies across repeated simulations.

---

## 🧠 Methodology

### Elo Rating

Each team starts with an initial rating.

After every match, ratings are updated according to the difference between the expected and actual result.

### UCLytics Strength Score

The custom strength score combines:

* Points efficiency
* Win rate
* Goals per game
* Goals conceded per game
* Goal difference

The score is intended as an analytical indicator rather than an official UEFA rating.

### Tournament Simulation

The simulator converts relative team strength into approximate scoring rates and generates match scores using a Poisson distribution.

Thousands of tournaments can then be simulated to examine how frequently each selected team wins the simulated competition.

---

## 🛠 Tech Stack

* Python
* Pandas
* NumPy
* Plotly
* Streamlit

---

## 📁 Project Structure

```text
UCLYTICS/
│
├── app.py
├── data.csv
├── requirements.txt
├── README.md
└── .devcontainer/
```

---

## ▶️ Run Locally

Install the dependencies:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
streamlit run app.py
```

---

## 🗺 Roadmap

* [x] Initial Streamlit dashboard
* [x] Team statistics
* [x] Team comparison
* [x] Team Scout
* [x] Power Rankings
* [x] Elo ratings
* [x] Tournament simulator
* [ ] Complete 2025/26 match dataset
* [ ] Public deployment
* [ ] Interactive match explorer
* [ ] 2026/27 data updates
* [ ] Improved rating model
* [ ] Player-level analytics

---

## 🎯 Project Motivation

Football produces enormous amounts of data, but raw match statistics can be difficult to interpret.

UCLytics explores how data can be transformed into a simple product that helps users understand team performance, compare clubs and experiment with different tournament scenarios.

The project combines data engineering, analytics, statistical modelling, visualisation and product design.

---

## ⚠️ Disclaimer

UCLytics is an independent data-analysis project.

Ratings and simulations are model outputs and are not official UEFA rankings or predictions of actual tournament results.

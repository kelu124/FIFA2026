# FIFA World Cup 2026 — Predictions Tracker

This repo tracks **Luc's match predictions** for the 2026 FIFA World Cup hosted across the USA, Canada, and Mexico.

## Files

| File | Purpose |
|------|---------|
| [`predictions.md`](predictions.md) | Match-by-match predictions, actual scores, and points earned |
| [`standings.md`](standings.md) | Group standings and bracket progression |
| [`scoring.md`](scoring.md) | Point system for evaluating predictions |

## Tools

| Path | Purpose |
|------|---------|
| [`scripts/predict_score.py`](scripts/predict_score.py) | Poisson scoreline predictor from betting-market odds |
| [`skills/match-odds-score-predictor.md`](skills/match-odds-score-predictor.md) | Step-by-step workflow for generating a match prediction |

## How it works

Before each match, Luc records his predicted score. After the match, the actual score is filled in and points are awarded based on the [scoring rules](scoring.md).

To generate a model-based prediction, follow the [match-odds-score-predictor](skills/match-odds-score-predictor.md) skill — it fetches betting odds, runs the Poisson model via `scripts/predict_score.py`, and outputs a ranked scoreline shortlist.

---

*FIFA World Cup 2026 runs June 11 – July 19, 2026.*

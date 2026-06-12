---
name: match-odds-score-predictor
description: Predicts a likely scoreline for a football/soccer match by converting bookmaker and prediction-market odds (1X2 moneyline, draw, over/under total goals) into a calibrated Poisson scoring model.
---

# Match Odds → Scoreline Predictor

Turns betting-market consensus (1X2 odds + total-goals line) into a ranked list
of likely final scores using an independent-Poisson goal model.

## Workflow

### Step 1 — Find the odds for the match

Search the web for the specific fixture. Good queries:
- `"<Team A> vs <Team B> odds oddsportal"`
- `"<Team A> vs <Team B> odds oddschecker"`
- `"<Team A> vs <Team B> 1X2 draw odds"`
- `"Polymarket <Team A> <Team B>"` or `"Kalshi <Team A> <Team B>"` for cross-check

You need:
1. **1X2 / moneyline odds**: Team A win, Draw, Team B win
2. **Total goals line + Over/Under odds** (usually 2.5 line)
3. *(Optional)* Prediction-market win probability to sanity-check

If prediction market disagrees with de-vigged bookmaker by >5 points, say so and consider averaging.

### Step 2 — Run the predictor script

```bash
python3 scripts/predict_score.py \
  --team1 "<Team A>" --team2 "<Team B>" \
  --ml1 <Team A moneyline> \
  --draw <draw odds> \
  --ml2 <Team B moneyline> \
  --over <over odds> \
  --under <under odds> \
  --line <total goals line, default 2.5> \
  --top 10
```

Odds can be American (`-120`, `+365`) or decimal (`1.83`, `4.65`) -- formats can be mixed.

The script will:
1. Convert raw odds to implied probabilities and show bookmaker overround
2. De-vig 1X2 and Over/Under into "true" probabilities
3. Solve for total expected goals matching de-vigged Over/Under
4. Split lambda_total between teams to match de-vigged 1X2
5. Print top N most likely scorelines with probabilities

### Step 3 — Present the result

- Lead with calibrated expected goals (lambda1 / lambda2)
- Give top 2-3 scorelines with probabilities as a ranked shortlist (not a single confident forecast)
- Mention if prediction-market cross-check agreed with bookmaker numbers
- Always include: independent Poisson slightly under-weights draws (Dixon-Coles effect); model only knows what is priced into the odds

## Notes & edge cases

- **Different total-goals lines**: pass via `--line` (e.g. `--line 3.5`)
- **No draw market** (knockout stage): script assumes 3-way market -- flag to user
- **Multiple bookmakers disagree**: prefer aggregator consensus or average
- **Sanity check**: lambda1 + lambda2 approx lambda_total; model-implied 1X2 should be within a couple of points of de-vigged input

#!/usr/bin/env python3
"""
predict_score.py — Predict football/soccer scorelines from betting-market odds.

Takes 1X2 (match-result) odds and an Over/Under total-goals line, de-vigs them
into "true" probabilities, calibrates an independent-Poisson goal-scoring model
against those probabilities, and prints the resulting expected goals plus the
most likely scorelines.

Odds may be given in American format (e.g. -120, +250, +365) or decimal
format (e.g. 1.83, 3.50, 4.65). Mixing formats in one call is fine.

EXAMPLE (Canada vs Bosnia, World Cup 2026 Group B opener):

    python predict_score.py \
        --team1 "Canada" --team2 "Bosnia" \
        --ml1 -120 --draw +250 --ml2 +365 \
        --over +120 --under -160 --line 2.5 \
        --top 10
"""

import argparse
import math


def parse_odds(odds_str):
    s = str(odds_str).strip()
    if s and s[0] in "+-":
        val = float(s)
        if val > 0:
            return 1.0 + val / 100.0
        else:
            return 1.0 + 100.0 / abs(val)
    val = float(s)
    if val <= 1.0:
        raise ValueError(f"Decimal odds must be > 1.0, got {val}")
    return val


def implied_prob(decimal_odds):
    return 1.0 / decimal_odds


def devig(probs):
    total = sum(probs)
    return [p / total for p in probs]


def poisson_pmf(k, lam):
    return math.exp(-lam) * lam ** k / math.factorial(k)


def poisson_cdf(k, lam):
    return sum(poisson_pmf(i, lam) for i in range(0, k + 1))


def solve_lambda_total(p_under, max_goals_under, lo=0.05, hi=8.0, iters=100):
    def f(lam):
        return poisson_cdf(max_goals_under, lam) - p_under
    for _ in range(iters):
        mid = (lo + hi) / 2.0
        if f(mid) > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def match_outcome_probs(lam1, lam2, max_goals=10):
    p1 = [poisson_pmf(i, lam1) for i in range(max_goals + 1)]
    p2 = [poisson_pmf(i, lam2) for i in range(max_goals + 1)]
    win1 = draw = win2 = 0.0
    for h in range(max_goals + 1):
        for a in range(max_goals + 1):
            p = p1[h] * p2[a]
            if h > a:
                win1 += p
            elif h == a:
                draw += p
            else:
                win2 += p
    return win1, draw, win2


def fit_lambdas(p1_target, draw_target, p2_target, lambda_total,
                max_goals=10, steps=2000):
    best = None
    for i in range(1, steps):
        lam1 = lambda_total * i / steps
        lam2 = lambda_total - lam1
        if lam2 <= 0:
            continue
        w1, d, w2 = match_outcome_probs(lam1, lam2, max_goals)
        err = (w1 - p1_target) ** 2 + (d - draw_target) ** 2 + (w2 - p2_target) ** 2
        if best is None or err < best[0]:
            best = (err, lam1, lam2, w1, d, w2)
    return best


def score_matrix(lam1, lam2, max_goals=6):
    p1 = [poisson_pmf(i, lam1) for i in range(max_goals + 1)]
    p2 = [poisson_pmf(i, lam2) for i in range(max_goals + 1)]
    matrix = {}
    for h in range(max_goals + 1):
        for a in range(max_goals + 1):
            matrix[(h, a)] = p1[h] * p2[a]
    return matrix


def top_scorelines(matrix, n=10):
    return sorted(matrix.items(), key=lambda kv: -kv[1])[:n]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--team1", default="Team 1")
    ap.add_argument("--team2", default="Team 2")
    ap.add_argument("--ml1", required=True)
    ap.add_argument("--draw", required=True)
    ap.add_argument("--ml2", required=True)
    ap.add_argument("--over", required=True)
    ap.add_argument("--under", required=True)
    ap.add_argument("--line", type=float, default=2.5)
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--max-goals", type=int, default=6)
    args = ap.parse_args()

    raw_1x2 = [implied_prob(parse_odds(args.ml1)),
               implied_prob(parse_odds(args.draw)),
               implied_prob(parse_odds(args.ml2))]
    overround_1x2 = sum(raw_1x2)

    raw_ou = [implied_prob(parse_odds(args.over)),
              implied_prob(parse_odds(args.under))]
    overround_ou = sum(raw_ou)

    p1, pd, p2 = devig(raw_1x2)
    p_over, p_under = devig(raw_ou)

    floor_goals = int(math.floor(args.line))
    lambda_total = solve_lambda_total(p_under, floor_goals)

    err, lam1, lam2, fw1, fd, fw2 = fit_lambdas(p1, pd, p2, lambda_total)

    matrix = score_matrix(lam1, lam2, max_goals=args.max_goals)
    top = top_scorelines(matrix, n=args.top)

    print("=" * 70)
    print(f"{args.team1} vs {args.team2}")
    print("=" * 70)
    print(f"\n[1] Raw implied probabilities")
    print(f"  {args.team1}: {raw_1x2[0]*100:5.1f}%   Draw: {raw_1x2[1]*100:5.1f}%   "
          f"{args.team2}: {raw_1x2[2]*100:5.1f}%   (sum = {overround_1x2*100:.1f}%)")
    print(f"  Over {args.line}: {raw_ou[0]*100:5.1f}%   Under {args.line}: {raw_ou[1]*100:5.1f}%   "
          f"(sum = {overround_ou*100:.1f}%)")
    print(f"\n[2] De-vigged ('true') probabilities")
    print(f"  {args.team1}: {p1*100:5.1f}%   Draw: {pd*100:5.1f}%   {args.team2}: {p2*100:5.1f}%")
    print(f"  Over {args.line}: {p_over*100:5.1f}%   Under {args.line}: {p_under*100:5.1f}%")
    print(f"\n[3] Calibrated Poisson model")
    print(f"  Total expected goals: {lambda_total:.3f}")
    print(f"  {args.team1} xG: {lam1:.3f}")
    print(f"  {args.team2} xG: {lam2:.3f}")
    print(f"  Model 1X2: {args.team1} {fw1*100:.1f}% / Draw {fd*100:.1f}% / "
          f"{args.team2} {fw2*100:.1f}%  (fit error: {err:.2e})")
    print(f"\n[4] Top {args.top} most likely scorelines")
    total_shown = 0.0
    for (h, a), p in top:
        total_shown += p
        print(f"  {args.team1} {h}-{a} {args.team2}:  {p*100:5.2f}%")
    print(f"  (top {args.top} scorelines cover {total_shown*100:.1f}% of probability mass)")


if __name__ == "__main__":
    main()

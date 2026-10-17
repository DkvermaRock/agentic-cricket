"""Seeded, illustrative batting model; the renderer consumes outcomes, never decides them."""
from __future__ import annotations

import copy
import math
import random
import statistics

RULES = "boundary-v2"
ACTIONS = ["defend", "drive", "pull", "loft"]
LENGTHS = ["full", "good", "short"]
LINES = ["off", "middle", "leg"]
ATTRIBUTES = ["power", "timing", "composure"]
FIT = {"full": [0.7, 1.0, 0.05, 0.75], "good": [0.95, 0.55, 0.2, 0.3], "short": [0.4, 0.0, 1.0, 0.5]}


def cost(player):
    return 10 + sum(math.floor(player[k] ** 2 / 300 + 0.5) for k in ATTRIBUTES)


def context(rng):
    return rng.choice(LENGTHS) + ":" + rng.choice(LINES)


def choose(policy, ctx, rng, heuristic=False):
    if heuristic:
        return "pull" if ctx.startswith("short") else "drive"
    values = policy.get(ctx)
    if values:
        return ACTIONS[max(range(4), key=lambda a: values[a][1] / max(values[a][0], 1))]
    return rng.choices(ACTIONS, weights=[1, 4, 3, 2])[0]


def outcome(player, ctx, action, rng):
    length, line = ctx.split(":")
    i = ACTIONS.index(action)
    fit = FIT[length][i] - (0.1 if line == "off" and action == "pull" else 0)
    skill = (player["timing"] * 0.65 + player["composure"] * 0.35) / 100
    aggression = [0.0, 0.35, 0.45, 1.0][i]
    wicket_risk = max(0.012, 0.035 + (1 - fit) * 0.12 + aggression * 0.085 - skill * 0.05)
    # Always consume the same random draws so paired evaluation is meaningful.
    wicket_roll, contact_roll, run_roll = rng.random(), rng.random(), rng.random()
    if wicket_roll < wicket_risk:
        return 0, True
    if contact_roll > 0.28 + 0.45 * skill + 0.25 * fit:
        return 0, False
    if action == "defend":
        return (1 if run_roll < 0.3 else 0), False
    boundary = 0.05 + player["power"] / 100 * 0.3 + fit * 0.14
    if action == "loft" and run_roll < boundary:
        return 6, False
    if run_roll < boundary:
        return 4, False
    return (1 if run_roll < 0.72 else 2 if run_roll < 0.94 else 3), False


def play_over(player, policy, seed, target=12):
    rng = random.Random(seed)
    events, score = [], 0
    for ball in range(6):
        ctx = context(rng)
        action = choose(policy, ctx, rng)
        runs, out = outcome(player, ctx, action, rng)
        length, line = ctx.split(":")
        # Visual variation has its own RNG, independent of game results.
        visual = random.Random(seed * 31 + ball)
        angle = visual.uniform(-0.85, 0.8) if action != "pull" else visual.uniform(0.95, 1.55)
        distance = {0: 3.0, 1: 22.0, 2: 36.0, 3: 47.0, 4: 68.0, 6: 74.0}[runs]
        wicket_type = ("caught" if action == "loft" or length == "short" else "bowled") if out else None
        if wicket_type == "caught":
            distance = 30.0
        x = {"off": 0.45, "middle": 0.15, "leg": -0.1}[line]
        contact_y = {"full": 0.46, "good": 0.7, "short": 1.15}[length]
        if wicket_type == "bowled":
            contact_y = 0.45
        score += runs
        events.append({
            "ball": ball + 1, "context": ctx, "length": length, "line": line,
            "action": action, "runs": runs, "out": out, "wicket_type": wicket_type,
            "score": score, "speed_kph": visual.randint(128, 141),
            "duration": 8.5 + max(0, runs - 1) * 2.5 if runs in (1, 2, 3) else 8.5,
            "trajectory": {"release": [0.2, 2.1, -9.4], "bounce": [x, 0.045, {"full": 6.1, "good": 2.3, "short": -2.2}[length]],
                           "contact": [x, contact_y, 8.9],
                           "end": [math.sin(angle) * distance, 1.65 if wicket_type == "caught" else 0.055, -math.cos(angle) * distance],
                           "arc": 15.0 if runs == 6 else 7.0 if wicket_type == "caught" else 1.5 if runs == 4 else 0.65},
            "commentary": describe(action, runs, out, wicket_type),
        })
        if out or score >= target:
            break
    return {"seed": seed, "target": target, "score": score, "wickets": int(events[-1]["out"]),
            "won": score >= target, "events": events, "rules_version": RULES,
            "player_attributes": {k: player[k] for k in ATTRIBUTES}, "policy_snapshot": copy.deepcopy(policy)}


def describe(action, runs, out, wicket_type):
    if out:
        return "Through the defence. The stumps are broken." if wicket_type == "bowled" else "Up in the air. The fielder settles underneath it. Taken."
    if runs == 6:
        return "Clean contact. High over the rope. Six!"
    if runs == 4:
        return "Finds the gap beautifully. Racing away for four."
    if runs == 0:
        return "Watchful batting. No run from that delivery."
    return f"{action.capitalize()} into the field. They come back for {['', 'one', 'two', 'three'][runs]}."


def train(player, previous, seed, balls=2000):
    rng = random.Random(seed)
    policy = copy.deepcopy(previous)
    for _ in range(balls):
        ctx = context(rng)
        values = policy.setdefault(ctx, [[0, 0.0] for _ in ACTIONS])
        total = sum(v[0] for v in values) + 1
        a = max(range(4), key=lambda i: values[i][1] / values[i][0] + 3 * math.sqrt(math.log(total + 1) / values[i][0]) if values[i][0] else float("inf"))
        runs, out = outcome(player, ctx, ACTIONS[a], rng)
        values[a][0] += 1
        values[a][1] += runs - 6 * out
    return policy


def evaluate(player, before, candidate, seed):
    rng = random.Random(seed)
    differences, old, new, heuristic = [], [], [], []
    for _ in range(1200):
        ctx, sample = context(rng), rng.randrange(2**31)
        results = []
        for policy, baseline in [(before, False), (candidate, False), ({}, True)]:
            action = choose(policy, ctx, random.Random(sample + 1), baseline)
            runs, out = outcome(player, ctx, action, random.Random(sample))
            results.append((runs, int(out), runs - 6 * out))
        old.append(results[0]); new.append(results[1]); heuristic.append(results[2])
        differences.append(results[1][2] - results[0][2])
    delta = statistics.mean(differences)
    margin = 1.96 * statistics.stdev(differences) / math.sqrt(len(differences))
    def metrics(rows):
        return {"runs_per_ball": round(statistics.mean(r[0] for r in rows), 3),
                "wicket_rate": round(statistics.mean(r[1] for r in rows), 4),
                "utility": round(statistics.mean(r[2] for r in rows), 3)}
    return {"accepted": delta - margin > 0, "samples": len(differences), "evaluation_seed": seed,
            "utility_delta": {"mean": round(delta, 4), "low": round(delta - margin, 4), "high": round(delta + margin, 4)},
            "before": metrics(old), "candidate": metrics(new), "heuristic": metrics(heuristic)}


def lessons(policy):
    return [{"context": ctx, "action": choose(policy, ctx, random.Random(0)), "samples": sum(v[0] for v in values)} for ctx, values in sorted(policy.items())]

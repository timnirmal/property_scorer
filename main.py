# main.py
from score.scorer import PropertyScorer

# 1) Your user profile
profile = {
    "walk_dist":  { "mode":"nice_to_have", "target":1.0, "lower":0.5, "upper":1.5,
                    "direction":-1, "weight":4 },
    # "walk_time":  { "mode":"must_have",    "target":15.0,
    #                 "direction":-1, "weight":3 },
    # … add drive_dist, drive_time similarly …
}

# 2) Google raw data
properties = {
    "A": {"walk_dist":1.0, "walk_time":13.0},
    "B": {"walk_dist":1.2, "walk_time":16.0},
    "C": {"walk_dist":1.4, "walk_time":20.0},
}

# 3) Quality ratings
qualities = {
    "A": {"walk_dist":2, "walk_time":4},
    "B": {"walk_dist":1, "walk_time":3},
    "C": {"walk_dist":5, "walk_time":2},
}

if __name__ == "__main__":
    scorer = PropertyScorer(
        profile,
        must_have_tolerance=0.0,   # 0 → “hard” must-have
        margin_epsilon=1e-3,       # auto-nudge ±0.001 units if needed
        quality_floor=0.1          # so quality=1 still contributes 10%
    )

    for name, raw in properties.items():
        qual = qualities[name]
        score = scorer.score_property(raw, qual, verbose=False)
        print(f"=== {name} final score: {score:.3f} ===\n")

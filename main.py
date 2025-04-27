# main.py
from score.scorer import PropertyScorer

# ——— 1) Define your user’s profile ———
user_profile = {
    # "walk_dist":  {"mode":"must_have",    "target":1.0,  "direction":-1, "weight":4},
    "walk_dist":  {"mode":"nice_to_have",    "target":1.0, "lower":0.0, "upper":1.5,  "direction":-1, "weight":4},
    # "walk_time":  {"mode":"nice_to_have", "target":15.0, "lower":10.0, "upper":20.0, "direction":-1, "weight":3},
    # "drive_dist": {"mode":"nice_to_have", "target":7.0,  "lower":5.0,  "upper":10.0, "direction":-1, "weight":2},
    # "drive_time": {"mode":"nice_to_have", "target":15.0, "lower":10.0, "upper":20.0, "direction":-1, "weight":1},
}

# ——— 2) Raw Google data for each property ———
properties_raw = {
    "A": {"walk_dist":1.0, "walk_time":13.0, "drive_dist":1.1, "drive_time":2.0},
    "B": {"walk_dist":1.2, "walk_time":16.0, "drive_dist":2.7, "drive_time":5.0},
    "C": {"walk_dist":1.4, "walk_time":20.0, "drive_dist":1.6, "drive_time":3.0},
}

# ——— 3) Quality ratings (1…5) for each factor/property ———
properties_qual = {
    "A": {"walk_dist":2, "walk_time":4, "drive_dist":5, "drive_time":5},
    "B": {"walk_dist":1, "walk_time":3, "drive_dist":4, "drive_time":4},
    "C": {"walk_dist":5, "walk_time":2, "drive_dist":3, "drive_time":3},
}


if __name__ == "__main__":
    scorer = PropertyScorer(user_profile)

    for name, raw in properties_raw.items():
        qual  = properties_qual[name]
        # score = scorer.score_property(raw, qual, verbose=True)
        score = scorer.score_property(raw, qual)
        print(f"Property {name}: final score = {score:.3f}")

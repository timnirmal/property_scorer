# main.py

from score.scorer import PropertyScorer

# user says “yes” to train station → we use nice_to_have decay from 0.5→1.5km
profile = {
    "train_dist": {
        "mode":      "nice_to_have",
        "target":    0.5,
        "lower":     0.5,
        "upper":     1.5,
        "direction": -1,
        "weight":    4,
    },
    # if user says “no”, just use mode="irrelevant"
}

properties = {
    "A": {"train_dist": 0.1},
    "B": {"train_dist": 1.4},
    "C": {"train_dist": 1.5},
}

qualities = {
    # "A": {"train_dist": 5},  # has quality
    "A": {},  # has quality
    "B": {},                 # no quality → raw-only
    "C": {},
}

scorer = PropertyScorer(
    profile,
    quality_floor=0.1,
    quality_weight=0.8,
    qual_exp=2.0,       # warp quality with e^x
    raw_floor=0.05,
)

for name in properties:
    print(f"--- {name} ---")
    score = scorer.score_property(properties[name], qualities[name], verbose=True)
    print(f"{name} final score = {score:.3f}\n")

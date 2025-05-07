# ui/config.py

"""
Central definition of every scoring factor.
For the four “multi-POI” factors we set `multi=True` and
point `csv_column` at the JSON-list column in your CSV.
"""
FACTORS = {
    # # single-value factors
    # "walk_dist": {
    #     "label":      "Walking Distance (km)",
    #     "default": {
    #         "mode":      "nice_to_have",
    #         "target":    1.0,
    #         "lower":     0.5,
    #         "upper":     1.5,
    #         "direction": -1,
    #         "weight":    4,
    #     },
    #     "csv_column": "train_walking_distance",
    #     "qual_method":"lower_is_better",
    # },
    # "walk_time": {
    #     "label":      "Walking Time (min)",
    #     "default": {
    #         "mode":      "must_have",
    #         "target":    15.0,
    #         "direction": -1,
    #         "weight":    3,
    #     },
    #     "csv_column": "train_walking_time",
    #     "qual_method":"lower_is_better",
    # },
    # "drive_dist": {
    #     "label":      "Driving Distance (km)",
    #     "default": {
    #         "mode":      "nice_to_have",
    #         "target":    3.0,
    #         "lower":     1.0,
    #         "upper":     5.0,
    #         "direction": -1,
    #         "weight":    2,
    #     },
    #     "csv_column": "train_driving_distance",
    #     "qual_method":"lower_is_better",
    # },
    # "drive_time": {
    #     "label":      "Driving Time (min)",
    #     "default": {
    #         "mode":      "must_have",
    #         "target":    20.0,
    #         "direction": -1,
    #         "weight":    2,
    #     },
    #     "csv_column": "train_driving_time",
    #     "qual_method":"lower_is_better",
    # },

    # nearest-train (still single)
    "train_dist": {
        "label":      "Train Distance (mins)",
        "default": {
            "mode":      "nice_to_have",
            "target":    1.0,
            "lower":     0.5,
            "upper":     1.5,
            "direction": -1,
            "weight":    4,
        },
        "csv_column":  "train_walking_time",
        "qual_method": "lower_is_better",
    },

    # multi-POI factors (lists in JSON)
    "school_dist": {
        "label":        "School Walking Time (mins)",
        "default": {
            "mode":      "must_have",   # schools are critical
            "target":    15.0,          # ideal: 15 min
            "lower":     5.0,           # very close: 5 min
            "upper":     30.0,          # still acceptable: 30 min
            "direction": -1,
            "weight":    4,
        },
        "csv_column":   "additional_schools",
        "qual_method":  "lower_is_better",
        "multi":        True,
        "multi_path":   "walking.travel_time",
        "aggregation":  "mean",
    },
    "hospital_dist": {
        "label":        "Hospital Walking Time (mins)",
        "default": {
            "mode":      "nice_to_have",
            "target":    10.0,          # ideal: 10 min
            "lower":     3.0,           # very close: 3 min
            "upper":     20.0,          # still acceptable: 20 min
            "direction": -1,
            "weight":    4,
        },
        "csv_column":   "additional_hospitals",
        "qual_method":  "lower_is_better",
        "multi":        True,
        "multi_path":   "walking.travel_time",
        "aggregation":  "mean",
    },
    "supermarket_dist": {
        "label":        "Supermarket Walking Time (mins)",
        "default": {
            "mode":      "nice_to_have",
            "target":    10.0,          # ideal: 10 min
            "lower":     5.0,           # very close: 5 min
            "upper":     20.0,          # still acceptable: 20 min
            "direction": -1,
            "weight":    4,
        },
        "csv_column":   "additional_supermarkets",
        "qual_method":  "lower_is_better",
        "multi":        True,
        "multi_path":   "walking.travel_time",
        "aggregation":  "mean",
    },
    "park_dist": {
        "label":        "Park Walking Time (mins)",
        "default": {
            "mode":      "nice_to_have",
            "target":    10.0,          # ideal: 10 min
            "lower":     5.0,           # very close: 5 min
            "upper":     20.0,          # still acceptable: 20 min
            "direction": -1,
            "weight":    4,
        },
        "csv_column":   "additional_parks",
        "qual_method":  "lower_is_better",
        "multi":        True,
        "multi_path":   "walking.travel_time",
        "aggregation":  "mean",
    },
}

# -----------------------------------------------------------------------------
# OPTIONAL DEFAULTS for any fields you omit above (so you can tweak in one spot)
# -----------------------------------------------------------------------------
OPTIONAL_DEFAULTS = {
    # multi-POI extraction path
    "multi_path":     "walking.travel_time",

    # aggregation defaults
    "aggregation":    "mean",
    "nearest_k":      1,
    "farthest_k":     1,
    "percentile":     0.5,

    # weighted-decay defaults
    "decay_function": None,    # or "exp", "quadratic"
    "decay_rate":     1.0,

    # quality method fallback
    "qual_method":    "lower_is_better",
}

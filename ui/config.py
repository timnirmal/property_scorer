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
        "label":      "Train Distance (km)",
        "default": {
            "mode":      "nice_to_have",
            "target":    1.0,
            "lower":     0.5,
            "upper":     1.5,
            "direction": -1,
            "weight":    4,
        },
        "csv_column": "train_walking_distance",
        "qual_method":"lower_is_better",
    },

    # multi-POI factors (lists in JSON)
    "school_dist": {
        "label":      "School Distance (km)",
        "default": {
            "mode":      "nice_to_have",
            "target":    1.0,
            "lower":     0.5,
            "upper":     1.5,
            "direction": -1,
            "weight":    4,
        },
        "csv_column": "additional_schools",   # JSON list
        "qual_method":"lower_is_better",
        "multi":     True,
    },
    "hospital_dist": {
        "label":      "Hospital Distance (km)",
        "default": {
            "mode":      "nice_to_have",
            "target":    2.0,
            "lower":     1.0,
            "upper":     3.0,
            "direction": -1,
            "weight":    4,
        },
        "csv_column": "additional_hospitals",
        "qual_method":"lower_is_better",
        "multi":     True,
    },
    "supermarket_dist": {
        "label":      "Supermarket Distance (km)",
        "default": {
            "mode":      "nice_to_have",
            "target":    1.0,
            "lower":     0.5,
            "upper":     2.0,
            "direction": -1,
            "weight":    4,
        },
        "csv_column": "additional_supermarkets",
        "qual_method":"lower_is_better",
        "multi":     True,
    },
    "park_dist": {
        "label":      "Park Distance (km)",
        "default": {
            "mode":      "nice_to_have",
            "target":    1.0,
            "lower":     0.2,
            "upper":     2.0,
            "direction": -1,
            "weight":    4,
        },
        "csv_column": "additional_parks",
        "qual_method":"lower_is_better",
        "multi":     True,
    },
}

# ui/config.py

"""
Define every factor here, with:
 - a human label
 - default ProfileScorer inputs
 - the CSV column name
 - (optionally) how to compute quality from the raw values
"""
FACTORS = {
    # "walk_dist": {
    #     "label":     "Walking Distance (km)",
    #     "default": {
    #         "mode":      "nice_to_have",
    #         "target":    1.0,
    #         "lower":     0.5,
    #         "upper":     1.5,
    #         "direction": -1,
    #         "weight":    4,
    #     },
    #     "csv_column": "train_walking_distance",
    #     "qual_method": "lower_is_better",
    # },
    # "walk_time": {
    #     "label":     "Walking Time (min)",
    #     "default": {
    #         "mode":      "must_have",
    #         "target":    15.0,
    #         "direction": -1,
    #         "weight":    3,
    #     },
    #     "csv_column": "train_walking_time",
    #     "qual_method": "lower_is_better",
    # },
    # "drive_dist": {
    #     "label":     "Driving Distance (km)",
    #     "default": {
    #         "mode":      "nice_to_have",
    #         "target":    3.0,
    #         "lower":     1.0,
    #         "upper":     5.0,
    #         "direction": -1,
    #         "weight":    2,
    #     },
    #     "csv_column": "train_driving_distance",
    #     "qual_method": "lower_is_better",
    # },
    # "drive_time": {
    #     "label":     "Driving Time (min)",
    #     "default": {
    #         "mode":      "must_have",
    #         "target":    20.0,
    #         "direction": -1,
    #         "weight":    2,
    #     },
    #     "csv_column": "train_driving_time",
    #     "qual_method": "lower_is_better",
    # },
}


# add the five “nearby” distance factors
for amenity in ["train", "hospital", "supermarket", "park", "school"]:
    key = f"{amenity}_dist"
    FACTORS[key] = {
        "label":      f"{amenity.capitalize()} Distance (km)",
        "default": {
            "mode":      "nice_to_have",
            "target":    1.0,
            "lower":     0.5,
            "upper":     1.5,
            "direction": -1,
            "weight":    4,
        },
        "csv_column": f"{amenity}_walking_distance",
        "qual_method":"lower_is_better",
    }


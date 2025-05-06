FACTORS = {
  "<factor_key>": {
     "label":       "Human-friendly label",
     "default": { … },       # default ProfileScorer params
     "csv_column":  "name_in_your_CSV_or_JSON",
     "qual_method": "how_to_compute_quality",
     # optional:
     "multi":       True|False
     "multi_path": "walking.distance",
     "aggregation": "mean|median|min|max|k-nearest|k-farthest"
  },
  … repeat for each factor …
}

label
- human-friendly label for the factor

default
- A dict matching the parameters that PropertyScorer expects:

```
"default": {
  "mode":      "nice_to_have",  // one of "must_have"|"nice_to_have"|"irrelevant"
  "target":    1.0,             // the “ideal” value
  "lower":     0.5,             // decay range lower bound
  "upper":     1.5,             // decay range upper bound
  "direction": -1,              // -1 = “smaller is better”, +1 = “larger is better”
  "weight":    4                // relative importance in the final blend
}
```

csv_column
- The exact column name (or JSON-list field) in your source data

qual_method
- "lower_is_better" → normalize so smaller distances → higher quality
- "higher_is_better" → normalize where larger raw values → higher quality.
- "mid_is_best" → score based on how close you are to the target.
- "binary" → treat as pass/fail, 1.0 if within range, 0.0 if not.
- "neutral" → no quality scoring, just use the raw value.
- weighted decay 
  - "decay_function": "exp",   // or "linear", "quadratic"
  - "decay_rate": 0.5
  - "add more if relevant"

multi (optional)
- A boolean indicating that this factor’s raw values are lists of multiple POIs per property.
- multi=false (default) → parse csv_column as a single numeric string ("2.3 km")
- multi=true → parse csv_column as JSON arrays of { name, walking, driving, … } and extract all "walking.distance" values

aggregation (optional)
- mean → average all the POI values 
- median → use the middle value (more robust to outliers)
- min → still only use the best (closest) one 
- max → still only use the worst (farthest) one
- k-nearest → average only the k closest ones, e.g., average the 3 closest school
  - "nearest_k": 3
- k-farthest → average only the k farthest ones, e.g., average the 3 farthest schools
  - "farthest_k": 3
- weighted decay 
  - "decay_function": "exp",   // or "linear", "quadratic"
  - "decay_rate": 0.5
- percentile thresholds
  - "percentile": 0.5

At scoring time we:
- Filter each list to those within the user’s [lower,upper] band 
- Average them (or zero-out if none in range)
- Feed that single float into the normal _raw_score logic


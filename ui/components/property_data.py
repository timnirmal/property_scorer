import json
import re
import streamlit as st
import pandas as pd

from ui.config import FACTORS, OPTIONAL_DEFAULTS


def _parse_numeric(val):
    """
    Parse a string or number into a float, handling:
      • Time: "1 hour 15 mins" → 75.0 (minutes)
              "5 mins" → 5.0
              "2 hr"  → 120.0
              "90 sec"→ 1.5
      • Distance: "2.3 km" → 2.3
                  "500 m"  → 0.5
      • Bare numbers: "42" → 42.0

    Returns:
        float or None if unparsable.
    """
    # Already numeric?
    if isinstance(val, (int, float)) and not pd.isna(val):
        return float(val)

    if not isinstance(val, str):
        return None

    s = val.strip().lower()

    # --- 1) TIME detection ---
    if any(unit in s for unit in ("hour", "hr", "min", "sec")):
        total_min = 0.0

        # hours → minutes
        hours = re.search(r'(\d+(?:\.\d+)?)\s*(?:h|hr|hour)', s)
        if hours:
            total_min += float(hours.group(1)) * 60

        # minutes
        mins = re.search(r'(\d+(?:\.\d+)?)\s*(?:m|min)', s)
        if mins:
            total_min += float(mins.group(1))

        # seconds → minutes
        secs = re.search(r'(\d+(?:\.\d+)?)\s*(?:s|sec)', s)
        if secs:
            total_min += float(secs.group(1)) / 60.0

        # if we found at least one of the above, return
        if hours or mins or secs:
            return total_min

    # --- 2) DISTANCE detection ---
    # kilometers
    km = re.search(r'([\d\.]+)\s*km\b', s)
    if km:
        return float(km.group(1))

    # meters → convert to km
    m = re.search(r'([\d\.]+)\s*m\b', s)
    if m:
        return float(m.group(1)) / 1000.0

    # --- 3) FALLBACK numeric ---
    num = re.search(r'([\d\.]+)', s)
    if num:
        try:
            return float(num.group(1))
        except ValueError:
            return None

    return None

def _calc_quality(values, method, cfg):
    """Map raw values → quality [0.1,0.9], or None if 'neutral'."""
    clean = [v for v in values if v is not None]
    n = len(values)
    if method == "neutral":
        return [None] * n

    if method == "binary":
        lb, ub = cfg["lower"], cfg["upper"]
        return [0.9 if (v is not None and lb <= v <= ub) else 0.1 for v in values]

    if method == "higher_is_better":
        if not clean or max(clean) == min(clean):
            return [0.5] * n
        mn, mx = min(clean), max(clean)
        return [0.1 + 0.8 * ((v - mn) / (mx - mn)) if v is not None else 0.5 for v in values]

    if method == "mid_is_best":
        t = cfg["target"]; rng = max(cfg["upper"] - cfg["lower"], 1e-12)
        return [0.9 - 0.8 * (abs(v - t) / rng) if v is not None else 0.5 for v in values]

    # default: lower_is_better
    if not clean or max(clean) == min(clean):
        return [0.5] * n
    mx, mn = max(clean), min(clean)
    return [0.1 + 0.8 * ((mx - v) / (mx - mn)) if v is not None else 0.5 for v in values]

def _extract_multi_path(poi_list, path: str):
    """
    Given a list of dicts and a dotted path (e.g. "walking.distance"),
    drill into each dict and return the numeric values found.
    """
    keys = path.split(".")
    out  = []
    for item in poi_list:
        val = item
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k)
            else:
                val = None
            if val is None:
                break
        num = _parse_numeric(val)
        if num is not None:
            out.append(num)
    return out

def create_property_data(active_factors: dict):
    st.header("Property Data")

    # 1) Load CSV
    try:
        df = pd.read_csv("penny2.csv")
    except Exception as e:
        st.error(f"Error reading penny2.csv: {e}")
        return {}, {}

    # 2) Sort by “Priority order”
    if "Priority order" in df.columns:
        df["_pr_num"] = pd.to_numeric(df["Priority order"], errors="coerce")
        df_num  = df[df["_pr_num"].notna()].sort_values("_pr_num", ascending=True)
        df_text = df[df["_pr_num"].isna()]
        df = pd.concat([df_num, df_text], ignore_index=True).drop(columns=["_pr_num"])
        priorities = df["Priority order"].astype(str).tolist()
    else:
        priorities = [None] * len(df)

    # 3) Reset index & bring Priority+Address to front
    df = df.reset_index(drop=True)
    display_cols = []
    if "Priority order" in df.columns:
        display_cols.append("Priority order")
    if "Address" in df.columns:
        display_cols.append("Address")
    display_cols += [c for c in df.columns if c not in display_cols]

    # 4) Compute addresses locally, *then* persist into session_state
    if "Address" in df.columns:
        addresses = df["Address"].astype(str).tolist()
    else:
        addresses = [f"Row {i+1}" for i in df.index]

    # Persist for other tabs / future calls
    st.session_state.property_order = addresses
    st.session_state.priority_map   = dict(zip(addresses, priorities))

    # 5) Show the sorted table
    st.dataframe(df[display_cols], hide_index=True, use_container_width=True)

    # 6) Parse each factor’s raw & quality
    raw_map, qual_map = {}, {}
    for key, use in active_factors.items():
        if not use:
            continue

        cfg       = FACTORS[key]
        col       = cfg["csv_column"]
        is_multi  = cfg.get("multi", False)

        # fill optional defaults
        multi_path   = cfg.get("multi_path", OPTIONAL_DEFAULTS["multi_path"])
        aggregation  = cfg.get("aggregation", OPTIONAL_DEFAULTS["aggregation"])
        nearest_k    = cfg.get("nearest_k", OPTIONAL_DEFAULTS["nearest_k"])
        farthest_k   = cfg.get("farthest_k", OPTIONAL_DEFAULTS["farthest_k"])
        percentile   = cfg.get("percentile", OPTIONAL_DEFAULTS["percentile"])
        decay_fn     = cfg.get("decay_function", OPTIONAL_DEFAULTS["decay_function"])
        decay_rate   = cfg.get("decay_rate", OPTIONAL_DEFAULTS["decay_rate"])
        qual_method  = cfg.get("qual_method", OPTIONAL_DEFAULTS["qual_method"])

        # ensure scorer sees them
        cfg.update({
            "multi_path":    multi_path,
            "aggregation":   aggregation,
            "nearest_k":     nearest_k,
            "farthest_k":    farthest_k,
            "percentile":    percentile,
            "decay_function":decay_fn,
            "decay_rate":    decay_rate,
        })

        if is_multi:
            raw_list = []
            for cell in df[col]:
                arr = json.loads(cell) if isinstance(cell, str) else cell or []
                raw_list.append(_extract_multi_path(arr, multi_path))
            qual_list = [None] * len(df)

        else:
            raw_list = []
            bad = False
            for cell in df[col]:
                n = _parse_numeric(cell)
                if n is None:
                    bad = True
                    n = 0.0
                raw_list.append(n)
            if bad:
                st.warning(f"Some '{col}' rows failed to parse → set to 0.0")
            qual_list = _calc_quality(raw_list, qual_method, cfg)

        raw_map[key]  = raw_list
        qual_map[key] = qual_list

    # 7) Build per-property dicts using the local `addresses`
    properties_data = {addr: {} for addr in addresses}
    qualities_data  = {addr: {} for addr in addresses}
    for key, vals in raw_map.items():
        for i, addr in enumerate(addresses):
            properties_data[addr][key] = vals[i]
            qualities_data [addr][key] = qual_map[key][i]

    return properties_data, qualities_data

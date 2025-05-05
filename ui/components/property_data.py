# ui/components/property_data.py

import json
import re
import streamlit as st
import pandas as pd
from ui.config import FACTORS

def _parse_numeric(val):
    """
    Extract the first float from "2.3 km" / "4 mins" / etc.
    Return None if unparsable.
    """
    if isinstance(val, str):
        m = re.search(r"([\d\.]+)", val)
        if m:
            try:
                return float(m.group(1))
            except ValueError:
                return None
    elif isinstance(val, (int, float)) and not pd.isna(val):
        return float(val)
    return None

def _calc_quality_lower_better(values):
    """
    Given a list of floats, map lower→higher quality in [0.1,0.9].
    """
    clean = [v for v in values if v is not None]
    if not clean or max(clean) == min(clean):
        return [0.5]*len(values)
    mx, mn = max(clean), min(clean)
    out = []
    for v in values:
        if v is None:
            out.append(0.5)
        else:
            q = (mx - v)/(mx - mn)
            out.append(max(0.1, min(0.9, q)))
    return out

def create_property_data(active_factors: dict):
    st.header("Property Data")

    # 1) Load CSV
    try:
        df = pd.read_csv("penny2.csv")
    except Exception as e:
        st.error(f"Error reading penny2.csv: {e}")
        return {}, {}

    # 2) Sort by “Priority order” (numeric first, then text)
    if "Priority order" in df.columns:
        df["_pr_num"] = pd.to_numeric(df["Priority order"], errors="coerce")
        df_num  = df[df["_pr_num"].notna()].sort_values("_pr_num", ascending=True)
        df_text = df[df["_pr_num"].isna()]
        df = pd.concat([df_num, df_text], ignore_index=True).drop(columns=["_pr_num"])
        priorities = df["Priority order"].astype(str).tolist()
    else:
        priorities = [None]*len(df)

    # 3) Reset index & bring Priority+Address to front
    df = df.reset_index(drop=True)
    display_cols = []
    if "Priority order" in df.columns:
        display_cols.append("Priority order")
    if "Address" in df.columns:
        display_cols.append("Address")
    display_cols += [c for c in df.columns if c not in display_cols]

    # 4) Remember ordering for later
    addresses = df["Address"].astype(str).tolist() if "Address" in df.columns \
                else [f"Row {i+1}" for i in df.index]
    st.session_state.property_order = addresses
    st.session_state.priority_map   = dict(zip(addresses, priorities))

    # 5) Show the sorted table
    st.dataframe(df[display_cols], hide_index=True, use_container_width=True)

    # 6) Parse each factor’s raw & quality
    raw_map, qual_map = {}, {}
    for key, use in active_factors.items():
        if not use:
            continue

        cfg      = FACTORS[key]
        col      = cfg["csv_column"]
        is_multi = cfg.get("multi", False)

        if col not in df.columns:
            st.warning(f"Column '{col}' missing → using empty")
            if is_multi:
                raw_list = [[]]*len(df)
                qual_list= [None]*len(df)
            else:
                raw_list = [0.0]*len(df)
                qual_list= _calc_quality_lower_better(raw_list)
        else:
            if is_multi:
                raw_list = []
                for cell in df[col]:
                    # cell could be a JSON string or Python list
                    arr = json.loads(cell) if isinstance(cell, str) else cell or []
                    dists = []
                    for rec in arr:
                        n = _parse_numeric(rec.get("walking",{}).get("distance",""))
                        if n is not None:
                            dists.append(n)
                    raw_list.append(dists)
                qual_list = [None]*len(df)   # no direct quality ratings
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
                qual_list = _calc_quality_lower_better(raw_list)

        raw_map[key]  = raw_list
        qual_map[key] = qual_list

    # 7) Build per-property dicts
    properties_data = {addr: {} for addr in addresses}
    qualities_data  = {addr: {} for addr in addresses}
    for key, vals in raw_map.items():
        for i, addr in enumerate(addresses):
            properties_data[addr][key] = vals[i]
            qualities_data[addr][key]  = qual_map[key][i]

    return properties_data, qualities_data

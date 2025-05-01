# ui/components/property_data.py

import re
import streamlit as st
import pandas as pd
from ui.config import FACTORS

def _parse_numeric(val):
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
    clean = [v for v in values if v is not None]
    if not clean or max(clean) == min(clean):
        return [0.5] * len(values)
    mx, mn = max(clean), min(clean)
    out = []
    for v in values:
        if v is None:
            out.append(0.5)
        else:
            q = (mx - v) / (mx - mn)
            out.append(max(0.1, min(0.9, q)))
    return out

def create_property_data(active_factors):
    st.header("Property Data")

    # 1) Load CSV
    try:
        df = pd.read_csv("penny2.csv")
    except Exception as e:
        st.error(f"Error reading penny2.csv: {e}")
        return {}, {}

    # 2) Sort by Priority order (numbers first, then text)
    if "Priority order" in df.columns:
        # coerce to numeric, NaN for text
        df["_pr_num"] = pd.to_numeric(df["Priority order"], errors="coerce")
        df_num  = df[df["_pr_num"].notna()].sort_values("_pr_num", ascending=True)
        df_text = df[df["_pr_num"].isna()]
        df = pd.concat([df_num, df_text], ignore_index=True).drop(columns=["_pr_num"])
        priorities = df["Priority order"].astype(str).tolist()
    else:
        priorities = [None] * len(df)

    # 3) Reset the index so we get 0..N-1 (and then hide it)
    df = df.reset_index(drop=True)

    # 4) Bring Priority & Address to front
    display_cols = []
    if "Priority order" in df.columns:
        display_cols.append("Priority order")
    if "Address" in df.columns:
        display_cols.append("Address")
    # add all the rest
    display_cols += [c for c in df.columns if c not in display_cols]

    # 5) Store ordering for calculation step
    if "Address" in df.columns:
        addresses = df["Address"].astype(str).tolist()
    else:
        addresses = [f"Row {i+1}" for i in df.index]

    st.session_state.property_order = addresses
    st.session_state.priority_map   = dict(zip(addresses, priorities))

    # 6) Display the sorted, re-ordered table hiding the index
    st.dataframe(
        df[display_cols],
        hide_index=True,
        use_container_width=True
    )

    # 7) Parse out each factor into raw_map & qual_map exactly as before
    raw_map, qual_map = {}, {}

    for key, use in active_factors.items():
        if not use:
            continue

        desired = FACTORS[key]["csv_column"]
        if desired in df.columns:
            col = desired
        else:
            # fallback: substring match
            candidates = [c for c in df.columns if desired.lower() in c.lower()]
            if len(candidates) == 1:
                col = candidates[0]
                st.info(f"Auto-matched `{key}` → `{col}`")
            elif len(candidates) > 1:
                col = st.selectbox(f"Select column for `{key}`", candidates, key=f"colsel_{key}")
            else:
                st.warning(f"No column found for `{key}`, using zeros")
                col = None

        # extract + parse
        if col:
            nums = []
            bad  = False
            for cell in df[col]:
                n = _parse_numeric(cell)
                if n is None:
                    bad = True
                    n = 0.0
                nums.append(n)
            if bad:
                st.warning(f"Some values in `{col}` failed to parse → set 0.0")
        else:
            nums = [0.0]*len(df)

        raw_map[key] = nums

        # quality
        if FACTORS[key].get("qual_method") == "lower_is_better":
            qual_map[key] = _calc_quality_lower_better(nums)
        else:
            qual_map[key] = [0.5]*len(df)

    # 8) Build per-property dicts in the sorted order
    properties_data = {addr: {} for addr in addresses}
    qualities_data  = {addr: {} for addr in addresses}

    for key, nums in raw_map.items():
        qs = qual_map[key]
        for i, addr in enumerate(addresses):
            properties_data[addr][key] = nums[i]
            qualities_data[addr][key]  = qs[i]

    return properties_data, qualities_data

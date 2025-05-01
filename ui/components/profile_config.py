# ui/components/profile_config.py

import streamlit as st
from ui.config import FACTORS

def create_property_inputs(factor_key, defaults):
    """Render the per-factor inputs and return a cfg dict."""
    info = FACTORS[factor_key]
    st.subheader(info["label"])

    col1, col2 = st.columns(2)
    with col1:
        mode = st.selectbox(
            "Mode",
            ["must_have", "nice_to_have", "irrelevant"],
            index=["must_have","nice_to_have","irrelevant"].index(defaults["mode"]),
            key=f"{factor_key}_mode"
        )
        target = st.number_input(
            "Target",
            value=float(defaults["target"]),
            key=f"{factor_key}_target"
        )
    with col2:
        direction = st.selectbox(
            "Direction",
            [-1, 1],
            index=0 if defaults["direction"]==-1 else 1,
            format_func=lambda x: "-1 (smaller better)" if x==-1 else "1 (larger better)",
            key=f"{factor_key}_direction"
        )
        weight = st.number_input(
            "Weight",
            min_value=0.1,
            value=float(defaults["weight"]),
            key=f"{factor_key}_weight"
        )

    # only show lower/upper when mode==nice_to_have
    if mode == "nice_to_have":
        col3, col4 = st.columns(2)
        with col3:
            lower = st.number_input(
                "Lower bound",
                value=float(defaults.get("lower", target)),
                key=f"{factor_key}_lower"
            )
        with col4:
            upper = st.number_input(
                "Upper bound",
                value=float(defaults.get("upper", target)),
                key=f"{factor_key}_upper"
            )
    else:
        lower = defaults.get("lower", target)
        upper = defaults.get("upper", target)

    return {
        "mode":      mode,
        "target":    target,
        "lower":     lower,
        "upper":     upper,
        "direction": direction,
        "weight":    weight,
    }

def create_profile_config(active_factors):
    st.header("Profile Configuration")
    profile = {}

    # loop through active_factors in config order
    for key, is_active in active_factors.items():
        if not is_active:
            continue
        defaults = FACTORS[key]["default"]
        cfg = create_property_inputs(key, defaults)
        profile[key] = cfg
        st.divider()

    # now the scorer params
    st.header("PropertyScorer Parameters")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        must_have_tolerance = st.number_input("Must-have tolerance", min_value=0.0, value=0.0)
    with col2:
        margin_epsilon = st.number_input("Margin epsilon", min_value=0.0, value=1e-3)
    with col3:
        quality_floor = st.number_input("Quality floor", min_value=0.0, max_value=1.0, value=0.1)
    with col4:
        quality_weight = st.number_input("Quality weight", min_value=0.0, max_value=1.0, value=0.8)

    return profile, {
        "must_have_tolerance": must_have_tolerance,
        "margin_epsilon":      margin_epsilon,
        "quality_floor":       quality_floor,
        "quality_weight":      quality_weight,
    }

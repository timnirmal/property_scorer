# ui/components/profile_config.py

import streamlit as st
from ui.config import FACTORS

def create_property_inputs(factor_key: str, defaults: dict) -> dict:
    """
    Render full inputs for non-amenity factors:
      Mode, Target, Lower, Upper, Direction, Weight
    """
    info  = FACTORS[factor_key]
    label = info["label"]
    st.subheader(label)

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
            format_func=lambda x: "-1 (smaller better)" if x == -1 else "1 (larger better)",
            index=0 if defaults["direction"] == -1 else 1,
            key=f"{factor_key}_direction"
        )
        weight = st.number_input(
            "Weight",
            min_value=0.1,
            value=float(defaults["weight"]),
            key=f"{factor_key}_weight"
        )

    lower = defaults.get("lower", defaults["target"])
    upper = defaults.get("upper", defaults["target"])
    if mode == "nice_to_have":
        col3, col4 = st.columns(2)
        with col3:
            lower = st.number_input(
                "Lower bound",
                value=float(lower),
                key=f"{factor_key}_lower"
            )
        with col4:
            upper = st.number_input(
                "Upper bound",
                value=float(upper),
                key=f"{factor_key}_upper"
            )

    return {
        "mode":      mode,
        "target":    target,
        "lower":     lower,
        "upper":     upper,
        "direction": direction,
        "weight":    weight,
    }


def create_profile_config(active_properties: dict):
    """
    Build the profile configuration:
      1) For each nearby amenity, ask yes/no → then min/max time + direction + weight or mark irrelevant.
      2) For all other active_properties (walk_dist, walk_time, etc.), show full inputs.
      3) Collect global PropertyScorer parameters.
    """
    st.header("Profile Configuration")
    profile = {}

    # 1) Amenity toggles (now using walking time)
    st.subheader("Nearby Amenities (yes → set time range; no → ignore)")
    amenity_keys = ["train_dist", "hospital_dist", "supermarket_dist", "park_dist", "school_dist"]
    for key in amenity_keys:
        base_label = FACTORS[key]["label"].split("(")[0].strip()
        want = st.radio(
            f"Do you need {base_label}?",
            ("yes", "no"),
            key=f"need_{key}"
        )
        defaults = FACTORS[key]["default"]

        if want == "yes":
            cols1 = st.columns(2)
            with cols1[0]:
                min_t = st.number_input(
                    "Min walking time (mins)",
                    value=float(defaults["lower"]),
                    key=f"{key}_lower"
                )
            with cols1[1]:
                max_t = st.number_input(
                    "Max walking time (mins)",
                    value=float(defaults["upper"]),
                    key=f"{key}_upper"
                )
            cols2 = st.columns(2)
            with cols2[0]:
                direction = st.selectbox(
                    "Direction",
                    [-1, 1],
                    format_func=lambda x: "-1 (smaller better)" if x == -1 else "1 (larger better)",
                    index=0 if defaults["direction"] == -1 else 1,
                    key=f"{key}_direction"
                )
            with cols2[1]:
                weight = st.number_input(
                    "Weight",
                    min_value=0.1,
                    value=float(defaults["weight"]),
                    key=f"{key}_weight"
                )
            profile[key] = {
                "mode":      "nice_to_have",
                "target":    min_t,
                "lower":     min_t,
                "upper":     max_t,
                "direction": direction,
                "weight":    weight,
            }
        else:
            cfg = defaults.copy()
            cfg["mode"] = "irrelevant"
            profile[key] = cfg

        st.divider()

    # 2) Full inputs for the other factors
    st.subheader("Other Property Factors")
    for prop_key, is_active in active_properties.items():
        if not is_active or prop_key in amenity_keys:
            continue
        defaults = FACTORS[prop_key]["default"]
        cfg = create_property_inputs(prop_key, defaults)
        profile[prop_key] = cfg
        st.divider()

    # 3) Global PropertyScorer parameters
    st.header("PropertyScorer Parameters")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        must_have_tolerance = st.number_input(
            "Must-have tolerance",
            min_value=0.0,
            value=0.0,
            help="Soft band ± tol for must_have factors"
        )
    with col2:
        margin_epsilon = st.number_input(
            "Margin epsilon",
            min_value=0.0,
            value=1e-3,
            help="Auto-nudge when lower==target or upper==target"
        )
    with col3:
        quality_floor = st.number_input(
            "Quality floor",
            min_value=0.0, max_value=1.0,
            value=0.1,
            help="Min normalized quality (0…1)"
        )
    with col4:
        quality_weight = st.number_input(
            "Quality weight",
            min_value=0.0, max_value=1.0,
            value=0.8,
            help="Blend raw vs quality (0=raw only,1=quality only)"
        )

    scorer_params = {
        "must_have_tolerance": must_have_tolerance,
        "margin_epsilon":      margin_epsilon,
        "quality_floor":       quality_floor,
        "quality_weight":      quality_weight,
    }

    return profile, scorer_params

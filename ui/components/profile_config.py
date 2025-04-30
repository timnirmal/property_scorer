import streamlit as st

def create_property_inputs(property_name, default_mode, default_target, 
                          default_lower=None, default_upper=None, 
                          default_direction=-1, default_weight=3):
    """Create input fields for a property configuration."""
    st.subheader(f"{property_name}")
    col1, col2 = st.columns(2)
    
    with col1:
        mode = st.selectbox(
            f"Mode",
            ["must_have", "nice_to_have", "irrelevant"],
            index=["must_have", "nice_to_have", "irrelevant"].index(default_mode),
            key=f"{property_name}_mode"
        )
        
        target = st.number_input(
            f"Target",
            value=float(default_target),
            key=f"{property_name}_target"
        )
    
    with col2:
        direction = st.selectbox(
            f"Direction (-1: smaller is better, 1: larger is better)",
            [-1, 1],
            index=[0, 1].index(1) if default_direction == 1 else 0,
            key=f"{property_name}_direction"
        )
        
        weight = st.number_input(
            f"Weight",
            min_value=0.1,
            value=float(default_weight),
            key=f"{property_name}_weight"
        )
    
    # Only show lower/upper for nice_to_have
    if mode == "nice_to_have":
        col1, col2 = st.columns(2)
        with col1:
            lower = st.number_input(
                f"Lower bound",
                value=float(default_lower if default_lower is not None else target * 0.8),
                key=f"{property_name}_lower"
            )
        with col2:
            upper = st.number_input(
                f"Upper bound",
                value=float(default_upper if default_upper is not None else target * 1.2),
                key=f"{property_name}_upper"
            )
    else:
        lower = default_lower if default_lower is not None else target
        upper = default_upper if default_upper is not None else target
    
    return {
        "mode": mode,
        "target": target,
        "lower": lower,
        "upper": upper,
        "direction": direction,
        "weight": weight
    }

def create_profile_config(active_properties):
    """Create the profile configuration section."""
    st.header("Profile Configuration")
    
    profile = {}
    
    # Create property inputs based on active properties
    if active_properties["walk_dist"]:
        profile["walk_dist"] = create_property_inputs(
            "Walking Distance", "nice_to_have", 1.0, 0.5, 1.5, -1, 4
        )
        st.divider()

    if active_properties["walk_time"]:
        profile["walk_time"] = create_property_inputs(
            "Walking Time", "must_have", 15.0, None, None, -1, 3
        )
        st.divider()

    if active_properties["drive_dist"]:
        profile["drive_dist"] = create_property_inputs(
            "Driving Distance", "nice_to_have", 3.0, 1.0, 5.0, -1, 2
        )
        st.divider()

    if active_properties["drive_time"]:
        profile["drive_time"] = create_property_inputs(
            "Driving Time", "must_have", 20.0, None, None, -1, 2
        )
    
    # PropertyScorer parameters
    st.header("PropertyScorer Parameters")
    col1, col2, col3 = st.columns(3)

    with col1:
        must_have_tolerance = st.number_input(
            "Must-have tolerance",
            min_value=0.0,
            value=0.0,
            help="If >0, allow a 'soft' zone past target of ±tol"
        )

    with col2:
        margin_epsilon = st.number_input(
            "Margin epsilon",
            min_value=0.0,
            value=1e-3,
            help="Small auto-nudge when upper==target or lower==target"
        )

    with col3:
        quality_floor = st.number_input(
            "Quality floor",
            min_value=0.0,
            max_value=1.0,
            value=0.1,
            help="Minimum normalized quality (0…1)"
        )
    
    col4, col5, col6 = st.columns(3)
    with col4:
        quality_weight = st.number_input(
            "Quality weight",
            min_value=0.0,
            max_value=1.0,
            value=0.8,
            help="Weight for quality vs raw score blending (0…1)"
        )
    
    return profile, {
        "must_have_tolerance": must_have_tolerance,
        "margin_epsilon": margin_epsilon,
        "quality_floor": quality_floor,
        "quality_weight": quality_weight
    }
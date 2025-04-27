import streamlit as st
import pandas as pd
from io import StringIO
import sys
import os
import json
from datetime import datetime

# Import PropertyScorer
from score.scorer import PropertyScorer

# Set page title
st.title("PropertyScorer Experiment UI")

# Initialize session state for history
if 'history' not in st.session_state:
    st.session_state.history = []

# Create sidebar for property toggling
st.sidebar.header("Property Selection")
st.sidebar.write("Toggle which properties to include in the experiment:")

use_walk_dist = st.sidebar.checkbox("Walking Distance", value=True)
use_walk_time = st.sidebar.checkbox("Walking Time", value=True)
use_drive_dist = st.sidebar.checkbox("Driving Distance", value=False)
use_drive_time = st.sidebar.checkbox("Driving Time", value=False)

# Check if at least one property is selected
if not any([use_walk_dist, use_walk_time, use_drive_dist, use_drive_time]):
    st.error("Please select at least one property to continue.")
    st.stop()

# Main content area
st.write("Use this interface to experiment with the PropertyScorer by changing values and toggling properties.")

# Create tabs for different sections
tab1, tab2, tab3, tab4 = st.tabs(["Profile Configuration", "Property Data", "Run Calculation", "History"])

with tab1:
    # Function to create input fields for a property
    def create_property_inputs(property_name, default_mode, default_target, 
                              default_lower=None, default_upper=None, 
                              default_direction=-1, default_weight=3):
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

    # Create property inputs
    profile = {}
    
    st.header("Profile Configuration")
    
    if use_walk_dist:
        profile["walk_dist"] = create_property_inputs(
            "Walking Distance", "nice_to_have", 1.0, 0.5, 1.5, -1, 4
        )
        st.divider()

    if use_walk_time:
        profile["walk_time"] = create_property_inputs(
            "Walking Time", "must_have", 15.0, None, None, -1, 3
        )
        st.divider()

    if use_drive_dist:
        profile["drive_dist"] = create_property_inputs(
            "Driving Distance", "nice_to_have", 3.0, 1.0, 5.0, -1, 2
        )
        st.divider()

    if use_drive_time:
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

with tab2:
    # Function to create property data inputs
    def create_property_data(property_name):
        st.subheader(f"{property_name}")
        
        # Create a DataFrame for cleaner UI
        data = {
            "Property": ["A", "B", "C"],
            "Value": [
                1.0 if "dist" in property_name else 13.0,
                1.2 if "dist" in property_name else 16.0,
                1.4 if "dist" in property_name else 20.0
            ],
            "Quality (1-5)": [
                2 if property_name == "walk_dist" and "A" == "A" else 
                1 if property_name == "walk_dist" and "A" == "B" else
                5 if property_name == "walk_dist" and "A" == "C" else
                4 if property_name == "walk_time" and "A" == "A" else
                3 if property_name == "walk_time" and "A" == "B" else
                2 if property_name == "walk_time" and "A" == "C" else 3
            ]
        }
        
        df = pd.DataFrame(data)
        
        # Make the DataFrame editable
        edited_df = st.data_editor(
            df,
            key=f"{property_name}_editor",
            column_config={
                "Property": st.column_config.TextColumn("Property", disabled=True),
                "Value": st.column_config.NumberColumn("Value", min_value=0.0, format="%.2f"),
                "Quality (1-5)": st.column_config.NumberColumn("Quality (1-5)", min_value=1, max_value=5, step=1)
            },
            hide_index=True
        )
        
        # Extract the edited values
        result = {}
        for i, row in edited_df.iterrows():
            property_letter = row["Property"]
            result[property_letter] = {
                "val": row["Value"],
                "quality": row["Quality (1-5)"]
            }
        
        return result

    # Create data dictionaries
    st.header("Property Data")
    
    properties_data = {}
    qualities_data = {}

    for prop in profile.keys():
        prop_data = create_property_data(prop)
        st.divider()
        
        # Split into properties and qualities
        for property_name, data in prop_data.items():
            if property_name not in properties_data:
                properties_data[property_name] = {}
            if property_name not in qualities_data:
                qualities_data[property_name] = {}
            
            properties_data[property_name][prop] = data["val"]
            qualities_data[property_name][prop] = data["quality"]

with tab3:
    # Function to capture print output
    def capture_output(func, *args, **kwargs):
        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()
        
        result = func(*args, **kwargs)
        
        sys.stdout = old_stdout
        return result, mystdout.getvalue()

    # Run calculation button
    st.header("Run Calculation")
    
    if st.button("Run Calculation"):
        # Format profile for PropertyScorer
        formatted_profile = {}
        for prop, config in profile.items():
            formatted_profile[prop] = config

        # Create scorer
        scorer = PropertyScorer(
            formatted_profile,
            must_have_tolerance=must_have_tolerance,
            margin_epsilon=margin_epsilon,
            quality_floor=quality_floor
        )
        
        # Run calculations
        results = {}
        verbose_outputs = {}
        
        for name, raw in properties_data.items():
            qual = qualities_data[name]
            
            # Run without verbose
            score = scorer.score_property(raw, qual, verbose=False)
            results[name] = score
            
            # Run with verbose
            _, verbose_output = capture_output(
                scorer.score_property, raw, qual, verbose=True
            )
            verbose_outputs[name] = verbose_output
        
        # Store in history
        st.session_state.history.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "profile": formatted_profile.copy(),
            "properties": properties_data.copy(),
            "qualities": qualities_data.copy(),
            "params": {
                "must_have_tolerance": must_have_tolerance,
                "margin_epsilon": margin_epsilon,
                "quality_floor": quality_floor
            },
            "results": results.copy(),
            "verbose_outputs": verbose_outputs.copy(),
            "active_props": {
                "walk_dist": use_walk_dist,
                "walk_time": use_walk_time, 
                "drive_dist": use_drive_dist,
                "drive_time": use_drive_time
            }
        })
        
        # Display results
        st.header("Results")
        
        # Create results table
        results_data = [{"Property": name, "Score": f"{score:.3f}"} for name, score in results.items()]
        results_df = pd.DataFrame(results_data)
        
        st.dataframe(results_df, hide_index=True)
        
        # Show verbose outputs in expanders
        st.subheader("Verbose Output")
        for name, verbose in verbose_outputs.items():
            with st.expander(f"Property {name} verbose output"):
                st.text(verbose)

with tab4:
    # Display history
    st.header("Test History")
    
    if not st.session_state.history:
        st.info("No tests have been run yet. Configure parameters and run a calculation to see results here.")
    
    for i, entry in enumerate(reversed(st.session_state.history)):
        active_props = [prop for prop, is_active in entry["active_props"].items() if is_active]
        with st.expander(f"Test #{len(st.session_state.history) - i} - {entry['timestamp']} ({', '.join(active_props)})"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Profile")
                for prop, cfg in entry["profile"].items():
                    st.write(f"**{prop}**:")
                    for param, val in cfg.items():
                        st.write(f"- {param}: {val}")
                
                st.subheader("Parameters")
                for param, val in entry["params"].items():
                    st.write(f"- {param}: {val}")
            
            with col2:
                st.subheader("Properties")
                for name, props in entry["properties"].items():
                    st.write(f"**Property {name}**:")
                    for prop, val in props.items():
                        st.write(f"- {prop}: {val}")
                
                st.subheader("Qualities")
                for name, quals in entry["qualities"].items():
                    st.write(f"**Property {name}**:")
                    for prop, val in quals.items():
                        st.write(f"- {prop}: {val}")
            
            st.subheader("Results")
            results_data = [{"Property": name, "Score": f"{score:.3f}"} for name, score in entry["results"].items()]
            results_df = pd.DataFrame(results_data)
            st.dataframe(results_df, hide_index=True)
            
            st.subheader("Verbose Output")
            for name, verbose in entry["verbose_outputs"].items():
                with st.expander(f"Property {name} verbose output"):
                    st.text(verbose)
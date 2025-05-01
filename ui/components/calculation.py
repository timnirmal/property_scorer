# ui/components/calculation.py

import streamlit as st
import pandas as pd
from io import StringIO
import sys
from datetime import datetime
from score.scorer import PropertyScorer

def capture_output(func, *args, **kwargs):
    """Capture print output from a function call."""
    old_stdout = sys.stdout
    sys.stdout = mystdout = StringIO()
    result = func(*args, **kwargs)
    sys.stdout = old_stdout
    return result, mystdout.getvalue()

def run_calculation(profile, properties_data, qualities_data, scorer_params, active_properties):
    st.header("Run Calculation")

    if not st.button("Run Calculation"):
        return None, None

    # Build the scorer
    scorer = PropertyScorer(
        profile,
        must_have_tolerance=scorer_params["must_have_tolerance"],
        margin_epsilon=   scorer_params["margin_epsilon"],
        quality_floor=    scorer_params["quality_floor"],
        quality_weight=   scorer_params["quality_weight"],
    )

    # Retrieve sorted order and priorities from session_state
    order        = st.session_state.property_order
    priority_map = st.session_state.priority_map

    results = {}
    verbose_outputs = {}

    for addr in order:
        raw  = properties_data[addr]
        qual = qualities_data[addr]

        # compute
        score = scorer.score_property(raw, qual, verbose=False)
        results[addr] = score

        # verbose
        _, vb = capture_output(scorer.score_property, raw, qual, True)
        verbose_outputs[addr] = vb

    # Save to history
    if "history" not in st.session_state:
        st.session_state.history = []

    st.session_state.history.append({
        "timestamp":       datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "profile":         profile.copy(),
        "properties":      properties_data.copy(),
        "qualities":       qualities_data.copy(),
        "params":          scorer_params.copy(),
        "results":         results.copy(),
        "verbose_outputs": verbose_outputs.copy(),
        "active_props":    active_properties.copy(),
    })

    # --- Display results sorted by Priority ---
    st.header("Results")

    # Build a DataFrame so we can explicitly order columns
    results_table = []
    for addr in order:
        results_table.append({
            "Priority": priority_map.get(addr, ""),
            "Address":  addr,
            "Score":    results[addr],
        })

    df = pd.DataFrame(results_table)
    # reorder columns
    df = df.loc[:, ["Priority", "Address", "Score"]]
    # format Score to 3 decimals
    df["Score"] = df["Score"].map(lambda x: f"{x:.3f}")

    st.dataframe(
        df,
        hide_index=True,
        use_container_width=True
    )

    st.subheader("Verbose Output")
    for addr in order:
        with st.expander(f"{priority_map.get(addr,'')} – {addr}"):
            st.text(verbose_outputs[addr])

    return results, verbose_outputs

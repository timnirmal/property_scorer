# ui/components/calculation.py

import streamlit as st
import pandas as pd
from io import StringIO
import sys
from datetime import datetime

from score.scorer import PropertyScorer
from ui.config      import FACTORS

def capture_output(func, *args, **kwargs):
    """Capture stdout from func."""
    old, sys.stdout = sys.stdout, StringIO()
    result = func(*args, **kwargs)
    txt    = sys.stdout.getvalue()
    sys.stdout = old
    return result, txt

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

    # Which factors are multi-POI
    multi_keys = {k for k,v in FACTORS.items() if v.get("multi")}

    order        = st.session_state.property_order
    priority_map = st.session_state.priority_map

    results = {}
    verbose = {}

    for addr in order:
        raw  = properties_data[addr]
        qual = qualities_data[addr]

        # Build aggregated raw2 for scorer
        raw2 = {}
        # And collect per-factor verbose lines
        lines = [f"\n─ Property: {addr} (Priority {priority_map.get(addr,'')}) ─"]
        for key, x in raw.items():
            cfg = profile[key]
            label = FACTORS[key]["label"]

            if key in multi_keys:
                lows, highs = cfg["lower"], cfg["upper"]
                orig = x or []
                in_range = [d for d in orig if lows <= d <= highs]
                avg = sum(in_range)/len(in_range) if in_range else None

                lines.append(f"{label}:")
                lines.append(f"  • All distances ({len(orig)}): {orig}")
                lines.append(f"  • In [{lows}, {highs}] ({len(in_range)}): {in_range}")
                if avg is not None:
                    lines.append(f"  → Average = {avg:.3f}")
                    raw2[key] = avg
                else:
                    lines.append(f"  → None in range → raw_score=0")
                    # push out of band to force raw_score=0
                    raw2[key] = highs + 1.0

            else:
                # single value
                raw2[key] = x
                lines.append(f"{label}: x = {x}")

        # Now compute scores factor-by-factor
        total_w = 0.0
        sum_wfs = 0.0
        for key, x2 in raw2.items():
            cfg = profile[key]
            label = FACTORS[key]["label"]
            r = scorer._raw_score(x2, cfg)
            if r is None:
                continue
            if cfg["mode"] == "must_have" and r == 0.0:
                lines.append(f"{label}: must-have failed → total score = 0\n")
                results[addr] = 0.0
                verbose[addr] = "\n".join(lines)
                break

            q = qual.get(key)
            if q is None:
                fs = r
                lines.append(f"  • raw-only: r={r:.3f} → fs={fs:.3f} (w={cfg['weight']})")
            else:
                qn = scorer._qual_score(q)
                fs = (1-scorer.q_weight)*r + scorer.q_weight*qn
                lines.append(
                    f"  • blended: r={r:.3f}, qn={qn:.3f}, "
                    f"fs={(fs):.3f} (w={cfg['weight']})"
                )

            sum_wfs += cfg["weight"] * fs
            total_w += cfg["weight"]

        else:
            # only if no must-have break
            final = (sum_wfs / total_w) if total_w else 0.0
            lines.append(f"\n→ Final score = {final:.3f}\n")
            results[addr] = final
            verbose[addr] = "\n".join(lines)

    # Save history
    if "history" not in st.session_state:
        st.session_state.history = []
    st.session_state.history.append({
        "timestamp":       datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "profile":         profile.copy(),
        "properties":      properties_data.copy(),
        "qualities":       qualities_data.copy(),
        "params":          scorer_params.copy(),
        "results":         results.copy(),
        "verbose_outputs": verbose.copy(),
        "active_props":    active_properties.copy(),
    })

    # Display results
    st.subheader("Results")
    table = [
        {"Priority": priority_map.get(a,""), "Address": a, "Score": f"{results[a]:.3f}"}
        for a in order
    ]
    df = pd.DataFrame(table)
    st.dataframe(df, hide_index=True, use_container_width=True)

    # Show verbose
    st.subheader("Verbose Output")
    for addr in order:
        with st.expander(f"{priority_map.get(addr,'')} – {addr}"):
            st.text(verbose[addr])

    return results, verbose

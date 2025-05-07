# ui/components/calculation.py

import streamlit as st
import pandas as pd
import sys
from io import StringIO
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

def _color_scale(val):
    """
    Map a float 0.0→1.0 onto a green gradient:
      • 0.0 = very light,
      • 1.0 = dark green.
    Returns a CSS style string for pandas Styler.applymap.
    """
    try:
        v = float(val)
    except:
        return ""
    v = max(0.0, min(v, 1.0))
    # green component from 55→255
    g = int(55 + 200 * v)
    return f"background-color: rgb(0, {g}, 0); color: white;"

def run_calculation(profile,
                    properties_data,
                    qualities_data,
                    scorer_params,
                    active_properties):
    st.header("Run Calculation")
    if not st.button("Run Calculation"):
        return None, None

    scorer = PropertyScorer(
        profile,
        must_have_tolerance=scorer_params["must_have_tolerance"],
        margin_epsilon=   scorer_params["margin_epsilon"],
        quality_floor=    scorer_params["quality_floor"],
        quality_weight=   scorer_params["quality_weight"],
    )

    multi_keys   = {k for k, v in FACTORS.items() if v.get("multi")}
    order        = st.session_state.property_order
    priority_map = st.session_state.priority_map

    results       = {}
    verbose       = {}
    factor_scores = {}

    # ─── Compute all scores ─────────────────────────────────────────
    for addr in order:
        raw  = properties_data[addr]
        qual = qualities_data[addr]

        raw2 = {}
        lines = [f"\n─ Property: {addr} (Priority {priority_map.get(addr,'')}) ─"]

        # aggregate or pass through
        for key, x in raw.items():
            cfg   = profile[key]
            label = FACTORS[key]["label"]

            if key in multi_keys:
                lows, highs = cfg["lower"], cfg["upper"]
                orig = x or []
                in_range = [d for d in orig if lows <= d <= highs]
                avg = sum(in_range)/len(in_range) if in_range else None
                lines.append(f"{label}: all={orig}, in-band={in_range}")
                if avg is not None:
                    raw2[key] = avg
                    lines.append(f"  → avg={avg:.3f}")
                else:
                    raw2[key] = highs + 1.0
                    lines.append(f"  → none in range → force raw=0")
            else:
                raw2[key] = x
                lines.append(f"{label}: x={x}")

        total_w = 0.0
        sum_wfs = 0.0
        fs_map  = {}

        # score each factor
        for key, x2 in raw2.items():
            cfg   = profile[key]
            label = FACTORS[key]["label"]
            r     = scorer._raw(x2, cfg)
            if r is None:
                continue
            if cfg["mode"] == "must_have" and r == 0.0:
                lines.append(f"{label}: must-have failed → total=0")
                results[addr] = 0.0
                fs_map = {k: 0.0 for k in profile}
                break

            q = qual.get(key)
            if q is None:
                fs = r
                lines.append(f"  • {label} raw-only: r={r:.3f} → fs={fs:.3f}")
            else:
                qn = scorer._qual(q)
                fs = (r ** (1 - scorer.q_weight)) * (qn ** scorer.q_weight)
                lines.append(f"  • {label} blended: r={r:.3f}, qn={qn:.3f} → fs={fs:.3f}")

            fs_map[key]    = fs
            sum_wfs       += cfg["weight"] * fs
            total_w       += cfg["weight"]
        else:
            final = (sum_wfs / total_w) if total_w else 0.0
            results[addr] = final
            lines.append(f"→ Final score = {final:.3f}")

        verbose[addr]       = "\n".join(lines)
        factor_scores[addr] = fs_map

    # ─── Save history ────────────────────────────────────────────────
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

    # ─── Display a legend for score colors ───────────────────────────
    st.markdown("**Score color scale**")
    legend_html = """
    <div style="display:flex; align-items:center; gap:10px; margin-bottom:8px;">
      <span style="display:inline-block;width:20px;height:20px;background-color:rgb(0,55,0);"></span>0.00
      <span style="display:inline-block;width:20px;height:20px;background-color:rgb(0,105,0);"></span>0.25
      <span style="display:inline-block;width:20px;height:20px;background-color:rgb(0,155,0);"></span>0.50
      <span style="display:inline-block;width:20px;height:20px;background-color:rgb(0,205,0);"></span>0.75
      <span style="display:inline-block;width:20px;height:20px;background-color:rgb(0,255,0);"></span>1.00
    </div>
    """
    st.markdown(legend_html, unsafe_allow_html=True)

    # ─── Display overall results with color coding ────────────────────
    st.subheader("Results Summary")
    summary = [{
        "Priority": priority_map.get(addr, ""),
        "Address":  addr,
        "Score":    results.get(addr, 0.0),
    } for addr in order]
    df_summary = pd.DataFrame(summary)
    styled_summary = (
        df_summary.style
        .format("{:.3f}", subset=["Score"])
        .applymap(_color_scale, subset=["Score"])
    )
    st.dataframe(styled_summary, hide_index=True, use_container_width=True)

    # ─── Display per-factor breakdown ────────────────────────────────
    st.subheader("Breakdown by Factor")
    breakdown = []
    for addr in order:
        row = {"Priority": priority_map.get(addr, ""), "Address": addr}
        for key, fs in factor_scores.get(addr, {}).items():
            row[FACTORS[key]["label"]] = fs
        breakdown.append(row)

    df_break = pd.DataFrame(breakdown)
    factor_cols = df_break.columns.difference(["Priority", "Address"])
    styled_break = (
        df_break.style
        .format("{:.3f}", subset=factor_cols)
        .applymap(_color_scale, subset=factor_cols)
    )
    st.dataframe(styled_break, hide_index=True, use_container_width=True)

    # ─── Verbose output ──────────────────────────────────────────────
    st.subheader("Verbose Output")
    for addr in order:
        with st.expander(f"{priority_map.get(addr,'')} – {addr}"):
            st.text(verbose.get(addr, ""))

    return results, verbose

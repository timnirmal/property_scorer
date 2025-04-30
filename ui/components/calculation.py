import streamlit as st
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
    """Run the calculation and display results."""
    st.header("Run Calculation")
    
    if st.button("Run Calculation"):
        # Create scorer
        scorer = PropertyScorer(
            profile,
            must_have_tolerance=scorer_params["must_have_tolerance"],
            margin_epsilon=scorer_params["margin_epsilon"],
            quality_floor=scorer_params["quality_floor"],
            quality_weight=scorer_params["quality_weight"]
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
        if 'history' not in st.session_state:
            st.session_state.history = []
            
        st.session_state.history.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "profile": profile.copy(),
            "properties": properties_data.copy(),
            "qualities": qualities_data.copy(),
            "params": scorer_params.copy(),
            "results": results.copy(),
            "verbose_outputs": verbose_outputs.copy(),
            "active_props": active_properties.copy()
        })
        
        # Display results
        st.header("Results")
        
        # Create results table
        results_data = [{"Property": name, "Score": f"{score:.3f}"} for name, score in results.items()]
        st.dataframe(results_data, hide_index=True)
        
        # Show verbose outputs in expanders
        st.subheader("Verbose Output")
        for name, verbose in verbose_outputs.items():
            with st.expander(f"Property {name} verbose output"):
                st.text(verbose)
        
        return results, verbose_outputs
    
    return None, None
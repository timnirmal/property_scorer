import streamlit as st
import pandas as pd

def display_history():
    """Display the test history in a compact format."""
    st.header("Test History")
    
    if not st.session_state.history:
        st.info("No tests have been run yet. Configure parameters and run a calculation to see results here.")
        return
    
    # Create a table for quick comparison of test results
    summary_data = []
    for i, entry in enumerate(reversed(st.session_state.history)):
        test_num = len(st.session_state.history) - i
        active_props = [prop for prop, is_active in entry["active_props"].items() if is_active]
        
        # Get scores for each property
        scores = {f"Score {name}": f"{score:.3f}" for name, score in entry["results"].items()}
        
        # Create summary row
        summary_row = {
            "Test #": test_num,
            "Time": entry["timestamp"].split()[1],  # Just show time for compactness
            "Properties": ", ".join(active_props),
            **scores
        }
        summary_data.append(summary_row)
    
    # Display summary table
    if summary_data:
        st.subheader("Results Summary")
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, hide_index=True, use_container_width=True)
    
    # Detailed history with expanders
    st.subheader("Detailed Test History")
    for i, entry in enumerate(reversed(st.session_state.history)):
        active_props = [prop for prop, is_active in entry["active_props"].items() if is_active]
        test_num = len(st.session_state.history) - i
        
        # Create a compact summary of results
        results_summary = " | ".join([f"{name}: {score:.3f}" for name, score in entry["results"].items()])
        
        with st.expander(f"Test #{test_num} - {entry['timestamp']} - {results_summary}"):
            tab1, tab2, tab3 = st.tabs(["Configuration", "Data", "Results"])
            
            with tab1:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.caption("Active Properties")
                    st.write(", ".join(active_props))
                    
                    st.caption("PropertyScorer Parameters")
                    params_text = ", ".join([f"{param}: {val}" for param, val in entry["params"].items()])
                    st.write(params_text)
                
                with col2:
                    st.caption("Profile Configuration")
                    for prop, cfg in entry["profile"].items():
                        st.write(f"**{prop}**: {cfg['mode']}, target={cfg['target']}, weight={cfg['weight']}")
            
            with tab2:
                # Create data tables
                property_data = []
                for property_name in ["A", "B", "C"]:
                    if property_name in entry["properties"]:
                        row = {"Property": property_name}
                        
                        # Add raw values
                        for prop in active_props:
                            if prop in entry["properties"][property_name]:
                                row[f"{prop} (raw)"] = entry["properties"][property_name][prop]
                        
                        # Add quality values
                        for prop in active_props:
                            if prop in entry["qualities"][property_name]:
                                row[f"{prop} (qual)"] = entry["qualities"][property_name][prop]
                        
                        property_data.append(row)
                
                if property_data:
                    st.caption("Property Data and Quality Ratings")
                    df = pd.DataFrame(property_data)
                    st.dataframe(df, hide_index=True, use_container_width=True)
            
            with tab3:
                # Results
                st.caption("Final Scores")
                results_data = [{"Property": name, "Score": f"{score:.3f}"} for name, score in entry["results"].items()]
                results_df = pd.DataFrame(results_data)
                st.dataframe(results_df, hide_index=True)
                
                # Verbose output
                st.caption("Calculation Details")
                for name, verbose in entry["verbose_outputs"].items():
                    st.write(f"**Property {name} verbose output:**")
                    st.code(verbose, language="text")
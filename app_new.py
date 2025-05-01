import streamlit as st
import os

# # Setup score folder structure if needed
# if not os.path.exists('score'):
#     os.makedirs('score')
#
# # Copy scorer.py to score folder if not already there
# if not os.path.exists('score/scorer.py'):
#     with open('scorer.py', 'r') as f:
#         scorer_code = f.read()
#     with open('score/scorer.py', 'w') as f:
#         f.write(scorer_code)
        
# # Create __init__.py if not already there
# if not os.path.exists('score/__init__.py'):
#     with open('score/__init__.py', 'w') as f:
#         f.write('from .scorer import PropertyScorer\n\n__all__ = [\'PropertyScorer\']')

# Import UI components
from ui.components import (
    create_sidebar,
    create_profile_config,
    create_property_data,
    run_calculation,
    display_history
)

# Set light theme as default
st.set_page_config(
    page_title="PropertyScorer Experiment UI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=None
)

# Set page title
st.title("PropertyScorer Experiment UI")

# Initialize session state for history
if 'history' not in st.session_state:
    st.session_state.history = []

# Create sidebar and get active properties
active_properties = create_sidebar()

# Main content area
st.write("Use this interface to experiment with the PropertyScorer by changing values and toggling properties.")

# Create tabs for different sections
tab1, tab2, tab3, tab4 = st.tabs(["Profile Configuration", "Property Data", "Run Calculation", "History"])

with tab1:
    # Create profile configuration
    profile, scorer_params = create_profile_config(active_properties)

with tab2:
    # Create property data inputs
    properties_data, qualities_data = create_property_data(active_properties)

with tab3:
    # Run calculation and display results
    results, verbose_outputs = run_calculation(
        profile,
        properties_data,
        qualities_data,
        scorer_params,
        active_properties
    )

with tab4:
    # Display history
    display_history()
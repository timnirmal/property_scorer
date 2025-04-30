import streamlit as st
import pandas as pd

def create_property_data(active_properties):
    """Create the property data section with editable data tables."""
    st.header("Property Data")
    
    properties_data = {}
    qualities_data = {}

    for prop_name, is_active in active_properties.items():
        if not is_active:
            continue

        st.subheader(f"{prop_name}")
        
        # Default values based on property name
        default_values = {
            "walk_dist": [1.0, 1.2, 1.4],
            "walk_time": [13.0, 16.0, 20.0],
            "drive_dist": [2.0, 3.0, 4.0],
            "drive_time": [10.0, 15.0, 25.0]
        }
        
        default_qualities = {
            "walk_dist": [2, 1, 5],
            "walk_time": [4, 3, 2],
            "drive_dist": [3, 4, 2],
            "drive_time": [5, 3, 1]
        }
        
        # Create a DataFrame for cleaner UI
        data = {
            "Property": ["A", "B", "C"],
            "Value": default_values.get(prop_name, [1.0, 1.5, 2.0]),
            "Quality (1-5)": default_qualities.get(prop_name, [3, 3, 3])
        }
        
        df = pd.DataFrame(data)
        
        # Make the DataFrame editable
        edited_df = st.data_editor(
            df,
            key=f"{prop_name}_editor",
            column_config={
                "Property": st.column_config.TextColumn("Property", disabled=True),
                "Value": st.column_config.NumberColumn("Value", min_value=0.0, format="%.2f"),
                "Quality (1-5)": st.column_config.NumberColumn("Quality (1-5)", min_value=1, max_value=5, step=1)
            },
            hide_index=True
        )
        
        # Extract the edited values
        for i, row in edited_df.iterrows():
            property_letter = row["Property"]
            if property_letter not in properties_data:
                properties_data[property_letter] = {}
            if property_letter not in qualities_data:
                qualities_data[property_letter] = {}
            
            properties_data[property_letter][prop_name] = row["Value"]
            qualities_data[property_letter][prop_name] = row["Quality (1-5)"]
        
        st.divider()
    
    return properties_data, qualities_data
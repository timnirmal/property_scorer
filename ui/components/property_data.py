import streamlit as st
import pandas as pd

def create_property_data(active_properties):
    """Create the property data section using penny.csv data."""
    st.header("Property Data")
    
    # Read the CSV file
    try:
        df = pd.read_csv('penny.csv')
    except Exception as e:
        st.error(f"Error reading penny.csv: {e}")
        return {}, {}
    
    # Initialize column visibility in session state if not exists
    if 'column_visibility' not in st.session_state:
        # Initialize all columns as visible by default
        st.session_state.column_visibility = {}
    
    # Update column visibility for any new columns
    for col in df.columns:
        if col not in st.session_state.column_visibility:
            st.session_state.column_visibility[col] = True
    
    # Column visibility controls with search and select all/none
    st.subheader("Column Visibility")
    
    # Add search filter for columns
    search_term = st.text_input("Search columns", "").lower()
    
    # Add select all/none buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Select All"):
            for col in df.columns:
                st.session_state.column_visibility[col] = True
    with col2:
        if st.button("Select None"):
            for col in df.columns:
                st.session_state.column_visibility[col] = False
    
    # Create a grid layout for checkboxes
    filtered_columns = [col for col in df.columns if search_term in col.lower()]
    cols_per_row = 4
    for i in range(0, len(filtered_columns), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            if i + j < len(filtered_columns):
                col_name = filtered_columns[i + j]
                with col:
                    st.session_state.column_visibility[col_name] = st.checkbox(
                        col_name,
                        value=st.session_state.column_visibility[col_name],
                        key=f"visibility_{col_name}"
                    )
    
    # Filter columns based on visibility
    visible_columns = [col for col, visible in st.session_state.column_visibility.items() 
                      if visible]
    
    # Display filtered DataFrame
    st.dataframe(df[visible_columns], hide_index=True)
    
    # Extract data from CSV for scoring calculations
    properties_data = {}
    qualities_data = {}
    
    # Map property names to CSV columns
    property_mapping = {
        "walk_dist": "train_walking_distance",
        "walk_time": "train_walking_time",
        "drive_dist": "train_driving_distance",
        "drive_time": "train_driving_time"
    }
    
    # Calculate normalized quality scores (0-1 scale)
    def calculate_quality(values, property_type):
        if not values:
            return [0.5] * len(values)  # Default quality if no data
        max_val = max(values)
        min_val = min(values)
        if max_val == min_val:
            return [0.5] * len(values)  # Default quality if all values are same
        
        # For time/distance, lower values are better
        qualities = [(max_val - v) / (max_val - min_val) for v in values]
        return [max(0.1, min(0.9, q)) for q in qualities]  # Bound between 0.1 and 0.9
    
    # Extract data for each active property
    for prop, csv_col in property_mapping.items():
        if active_properties[prop]:
            if csv_col in df.columns:
                values = df[csv_col].tolist()
                properties_data[prop] = values
                qualities_data[prop] = calculate_quality(values, prop)
            else:
                st.warning(f"Column '{csv_col}' not found in the CSV file. Using default values.")
                num_rows = len(df)
                properties_data[prop] = [0.0] * num_rows  # Default to 0
                qualities_data[prop] = [0.5] * num_rows  # Default to neutral quality
    
    return properties_data, qualities_data
import streamlit as st

def create_sidebar():
    """Create and handle the sidebar for property selection."""
    st.sidebar.header("Property Selection")
    st.sidebar.write("Toggle which properties to include in the experiment:")

    use_walk_dist = st.sidebar.checkbox("Walking Distance", value=True)
    use_walk_time = st.sidebar.checkbox("Walking Time", value=False)
    use_drive_dist = st.sidebar.checkbox("Driving Distance", value=False)
    use_drive_time = st.sidebar.checkbox("Driving Time", value=False)

    # Check if at least one property is selected
    if not any([use_walk_dist, use_walk_time, use_drive_dist, use_drive_time]):
        st.error("Please select at least one property to continue.")
        st.stop()

    return {
        "walk_dist": use_walk_dist,
        "walk_time": use_walk_time,
        "drive_dist": use_drive_dist,
        "drive_time": use_drive_time
    }
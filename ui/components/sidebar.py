# ui/sidebar.py

import streamlit as st
from ui.config import FACTORS


def create_sidebar():
    st.sidebar.header("Property Selection")
    st.sidebar.write("Toggle which factors to include in the experiment:")

    active = {}
    for key, info in FACTORS.items():
        active[key] = st.sidebar.checkbox(info["label"], value=True)

    if not any(active.values()):
        st.sidebar.error("Please select at least one factor to continue.")
        st.stop()

    return active

import streamlit as st
import pandas as pd
from controllers.extract_data import average_inventory_time_report


df = average_inventory_time_report()

cols1, cols2, cols3 = st.columns([1, 1, 1], gap="medium")

with cols2:
    st.markdown(
        "<h4 style=text-align:center;>Average Inventory Time Report</h4>",
        unsafe_allow_html=True,
    )

st.write("")
st.write("")

st.dataframe(df, use_container_width=True, hide_index=True)

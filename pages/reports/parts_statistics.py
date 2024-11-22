import streamlit as st
import pandas as pd
from controllers.extract_data import parts_statistics_report


df = parts_statistics_report()

cols1, cols2, cols3 = st.columns([1, 1, 1], gap="medium")

with cols2:
    st.markdown(
        "<h4 style=text-align:center;>Parts Statistics Report</h4>",
        unsafe_allow_html=True,
    )

st.write("")
st.write("")

st.dataframe(
    df.style.format(
        {
            "Total Amount Spent": "${:,.2f}",
        }
    ),
    use_container_width=True,
    hide_index=True,
)

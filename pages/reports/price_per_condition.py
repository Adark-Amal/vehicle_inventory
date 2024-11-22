import streamlit as st
import pandas as pd
from controllers.extract_data import price_per_condition_report


df = price_per_condition_report()

cols1, cols2, cols3 = st.columns([1, 1, 1], gap="medium")

with cols2:
    st.markdown(
        "<h4 style=text-align:center;>Price Per Condition Report</h4>",
        unsafe_allow_html=True,
    )

st.write("")
st.write("")

st.dataframe(
    df.style.format(
        {
            "Excellent": "${:,.2f}",
            "Very Good": "${:,.2f}",
            "Good": "${:,.2f}",
            "Fair": "${:,.2f}",
        }
    ),
    use_container_width=True,
    hide_index=True,
)

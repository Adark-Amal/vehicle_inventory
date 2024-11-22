import streamlit as st
import pandas as pd
from controllers.extract_data import seller_history_report


df = seller_history_report()

cols1, cols2, cols3 = st.columns([1, 1, 1], gap="medium")

with cols2:
    st.markdown(
        "<h4 style=text-align:center;>Seller History Report</h4>",
        unsafe_allow_html=True,
    )

st.write("")
st.write("")
st.write("* Sellers in red may be overcharging for parts or ordering too many parts.")

# df['Avg Parts Quantity Per Vehicle'] = df['Avg Parts Quantity Per Vehicle'].apply(lambda x: f"${x:,.2f}")
# df['Avg Parts Cost Per Vehicle'] = df['Avg Parts Cost Per Vehicle'].apply(lambda x: f"${x:,.2f}")

st.dataframe(
    df.style.apply(
        lambda x: [
            (
                "background-color: red"
                if (x["Avg Parts Quantity Per Vehicle"] >= 5)
                or (x["Avg Parts Cost Per Vehicle"] >= 500)
                else ""
            )
            for _ in x
        ],
        axis=1,
    ).format(
        {
            "Avg Parts Quantity Per Vehicle": "${:,.2f}",
            "Avg Parts Cost Per Vehicle": "${:,.2f}",
            "Avg Purchase Price": "${:,.2f}",
        }
    ),
    use_container_width=True,
    hide_index=True,
)

import streamlit as st
import pandas as pd
from controllers.extract_data import monthly_sales_summary, monthly_sales_drilldown


df = monthly_sales_summary()

cols1, cols2, cols3 = st.columns([1, 1, 1], gap="medium")

with cols2:
    st.markdown(
        "<h4 style=text-align:center;>Monthly Sales Summary Report</h4>",
        unsafe_allow_html=True,
    )

st.write("")
st.write("")

# Add a 'Select' column to the DataFrame
df["Select"] = False
df["Gross Sales Income"] = df["Gross Sales Income"].apply(lambda x: f"${x:,.2f}")
df["Net Income"] = df["Net Income"].apply(lambda x: f"${x:,.2f}")
df["Year"] = df["Year"].apply(lambda x: f"{x:.0f}")

# Show the search results DataFrame with editable checkbox column
edited_df = st.data_editor(
    df,
    use_container_width=True,
    column_config={
        "Select": st.column_config.CheckboxColumn(
            "Select to View",
            help="Select this row to view details",
            default=False,
        ),
        "Year": st.column_config.Column("Year"),
        "Gross Sales Income": st.column_config.Column("Gross Sales Income"),
        "Net Income": st.column_config.Column("Net Income"),
    },
    hide_index=True,
)


# Capture selected rows based on the "Select" checkbox column
selected_rows = edited_df[edited_df["Select"] == True]

if not selected_rows.empty:

    # Store selected VIN in session state and navigate
    for _, row in selected_rows.iterrows():
        year = int(row["Year"])
        month = int(row["Month"])

        st.session_state["selected_year"] = year
        st.session_state["selected_month"] = month

    drilldown_df = monthly_sales_drilldown(year, month)

    if not drilldown_df.empty:
        cols1, cols2, cols3 = st.columns([1, 1, 1], gap="medium")

        with cols2:
            st.write("")
            st.write("")
            st.markdown(
                f"<h4 style=text-align:center;>Sales Details Report</h4>",
                unsafe_allow_html=True,
            )
        st.dataframe(
            drilldown_df.style.format(
                {
                    "Total Sales": "${:,.2f}",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.write("No sales data available for this month.")
else:
    col1, col2, col3 = st.columns([1, 1, 1], gap="medium")
    with col1:
        st.warning("Please select a row to drill down.")

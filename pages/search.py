import streamlit as st
import pandas as pd
from controllers.extract_data import (
    search_vehicles,
    get_vehicle_counts,
    fetch_distinct_values_from_table,
)
from utils.constants import (
    VIN_ACCESS_ROLES,
    STATUS_ACCESS_ROLES,
    VEHICLE_STATUS_OPTIONS,
    FUEL_TYPES,
)
from utils.auth import initialize_session_states, clear_search_results
from datetime import datetime


def render_page_title(user_role: str, pub_counts: int, pending_part: int) -> None:
    """
    Renders the page title and vehicle count information based on the user's role.

    Parameters:
        user_role (str): The role of the logged-in user.
        pub_counts (int): The number of vehicles available for sale.
        pending_part (int): The number of vehicles with pending parts.

    Returns:
        None
    """
    title_col = st.columns([1, 1, 1], gap="medium")
    with title_col[1]:
        st.markdown(
            "<p style='text-align:center; font-size:20px;'><b>NAA Vehicle Inventory</b></p>",
            unsafe_allow_html=True,
        )

    if user_role in ["Manager", "Inventory clerk", "Owner"]:
        with title_col[2]:
            st.markdown(
                f"<p style='text-align:right; font-size:20px;'><b>Total Vehicles with Pending Parts:</b> {pending_part}<br><b>Total Vehicles Available for Sale:</b> {pub_counts}</p>",
                unsafe_allow_html=True,
            )
    elif user_role in ["Public", "Salesperson"]:
        with title_col[2]:
            st.markdown(
                f"<p style='text-align:right; font-size:20px;'><b>Total Vehicles Available for Sale: {pub_counts}</b></p>",
                unsafe_allow_html=True,
            )


def fetch_filter_options() -> dict:
    """
    Fetches filter options (vehicle types, manufacturers, years, fuel types, colors) from the database.

    Parameters:
        None

    Returns:
        dict: A dictionary containing lists of available filter options.
    """

    max_year = datetime.now().year + 1

    # Fetch filter options using raw SQL
    vehicle_types = ["Any"] + fetch_distinct_values_from_table(
        "VehicleType", "vehicle_type"
    )
    manufacturers = ["Any"] + fetch_distinct_values_from_table(
        "VehicleManufacturer", "manufacturer_name"
    )
    years = ["Any"] + sorted(range(1980, max_year + 1))
    fuel_types = ["Any"] + FUEL_TYPES
    colors = ["Any"] + fetch_distinct_values_from_table("Color", "color_name")

    return {
        "vehicle_types": vehicle_types,
        "manufacturers": manufacturers,
        "years": years,
        "fuel_types": fuel_types,
        "colors": colors,
    }


def display_search_form(
    vehicle_types: list,
    manufacturers: list,
    years: list,
    fuel_types: list,
    colors: list,
    is_logged_in: bool,
    user_role: str,
) -> tuple:
    """
    Displays the search form with filters for vehicle search.

    Parameters:
        vehicle_types (list): List of available vehicle types.
        manufacturers (list): List of available manufacturers.
        years (list): List of available years.
        fuel_types (list): List of available fuel types.
        colors (list): List of available colors.
        is_logged_in (bool): Boolean indicating if the user is logged in.
        user_role (str): The role of the logged-in user.

    Returns:
        tuple: A tuple containing the selected filter values (vehicle_type, manufacturer, year, fuel_type, color, keyword, vin, vehicle_status)
    """
    col1, col2, col3 = st.columns([1, 1, 1], gap="medium")

    with col1:
        vehicle_type = st.selectbox("Vehicle Type", vehicle_types)
        manufacturer = st.selectbox("Manufacturer", manufacturers)

    with col2:
        year = st.selectbox("Year", years)
        fuel_type = st.selectbox("Fuel Type", fuel_types)

    with col3:
        color = st.selectbox("Color", colors)
        keyword = st.text_input("Keyword (search model, description)")

    vin = vehicle_status = None
    if is_logged_in:
        with col1:
            if user_role in VIN_ACCESS_ROLES:
                vin = st.text_input("VIN")

        with col2:
            if user_role in STATUS_ACCESS_ROLES:
                vehicle_status = st.radio(
                    "Vehicle Status", VEHICLE_STATUS_OPTIONS, horizontal=True
                )

    return (
        vehicle_type,
        manufacturer,
        year,
        fuel_type,
        color,
        keyword,
        vin,
        vehicle_status,
    )


def search_page() -> None:
    """
    Renders the search page interface with vehicle filters, total vehicle count, and role-based filters.
    """

    # Initialize session states
    initialize_session_states()

    # Check login status and user role
    is_logged_in = st.session_state.get("logged_in", False)
    user_role = st.session_state.get("role", "Public")

    # Clear reports section on logout or if user is not Manager or Owner
    if not is_logged_in or user_role not in ["Manager", "Owner"]:
        st.session_state["show_reports"] = False

    # Clear search results only if login status changes
    if st.session_state.get("prev_logged_in") != is_logged_in:
        clear_search_results()
        st.session_state["prev_logged_in"] = is_logged_in

    # Fetch vehicle counts
    pub_counts, pending_part = get_vehicle_counts()

    # Render page title and counts
    render_page_title(user_role, pub_counts, pending_part)

    # Fetch filter options
    filters = fetch_filter_options()

    # Initialize filters with None to avoid UnboundLocalError
    vin = None
    vehicle_status = None

    # Display search form and capture filter inputs
    vehicle_type, manufacturer, year, fuel_type, color, keyword, vin, vehicle_status = (
        display_search_form(
            filters["vehicle_types"],
            filters["manufacturers"],
            filters["years"],
            filters["fuel_types"],
            filters["colors"],
            is_logged_in,
            user_role,
        )
    )

    col1, col2, col3 = st.columns([1, 1, 1], gap="medium")

    with col1:
        st.write("")
        sub_col1, sub_col2, sub_col3 = st.columns([1, 1.5, 2.5], gap="small")
        with sub_col1:
            search_button = st.button("Search")

        with sub_col2:
            # Show "Show Reports" button only if the user is a Manager or Owner
            if is_logged_in and user_role in ["Manager", "Owner"]:
                if st.button("Show Reports"):
                    st.session_state["show_reports"] = not st.session_state[
                        "show_reports"
                    ]
                    st.rerun()

    if search_button:
        # Fetch search results
        results_df = search_vehicles(
            vehicle_type=vehicle_type,
            manufacturer=manufacturer,
            year=year,
            fuel_type=fuel_type,
            color=color,
            keyword=keyword,
            vin=vin if vin else None,
            vehicle_status=vehicle_status if vehicle_status else None,
            role=user_role,
        )

        # Store results in session state if not empty
        if not results_df.empty:
            st.session_state["search_results"] = results_df
            st.session_state["no_results"] = False
        else:
            st.session_state["search_results"] = None
            st.session_state["no_results"] = True

    # Display search results if available in session state
    if (
        "search_results" in st.session_state
        and st.session_state["search_results"] is not None
    ):
        df = st.session_state["search_results"]

        # Add an empty column for selection
        df["Select"] = False

        st.write("")
        st.write("")
        st.write("")
        # Show the search results DataFrame with editable checkbox column
        edited_df = st.data_editor(
            df,
            use_container_width=True,
            column_config={
                "Select": st.column_config.CheckboxColumn(
                    "Select to View",
                    help="Select this row to view details",
                    default=False,
                )
            },
            hide_index=True,
        )

        # Capture selected rows based on the "Select" checkbox column
        selected_rows = edited_df[edited_df["Select"] == True]["VIN"].tolist()

        view_button = st.button("View Selected Details")

        co1, co2, co3 = st.columns([1, 1, 1], gap="medium")
        with co1:
            st.warning("Select vehicle to view details")

        if view_button and selected_rows:
            st.session_state["selected_vin"] = selected_rows[0]
            # clear_search_results()  # Optionally clear if switching to details
            st.switch_page(st.Page("pages/details.py"))
    elif st.session_state.get("no_results", False):
        st.write("Sorry, it looks like we don’t have that in stock!")
        st.session_state["selected_vin"] = None


# Call search_page to render it whenever search.py is loaded
search_page()

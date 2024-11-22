import streamlit as st
from db.session import create_session
from controllers.extract_data import (
    lookup_customers,
    add_customer,
    add_vehicle_and_related_data,
    fetch_customer_id,
)
from datetime import datetime
from typing import List
import time


def fetch_vehicle_data() -> dict:
    """
    Fetches available vehicle types, manufacturers, and colors from the database.

    Parameters:
        None

    Returns:
        dict: Contains lists of vehicle types, manufacturers, and colors.
    """
    with create_session() as session:
        vehicle_types = session.execute(
            "SELECT vehicle_type FROM VehicleType"
        ).fetchall()
        manufacturer_options = session.execute(
            "SELECT manufacturer_name FROM VehicleManufacturer"
        ).fetchall()
        color_options = session.execute("SELECT color_name FROM Color").fetchall()

    return {
        "vehicle_types": [v[0] for v in vehicle_types],
        "manufacturers": [m[0] for m in manufacturer_options],
        "colors": [c[0] for c in color_options],
    }


def get_purchase_date() -> str:
    """
    Returns the current date formatted as YYYY-MM-DD for purchase date.

    Parameters:
        None

    Returns:
        str: The current date in YYYY-MM-DD format.
    """
    today_datetime = datetime.now()
    return today_datetime.strftime("%Y-%m-%d")


def validate_required_fields(fields: List[str]) -> bool:
    """
    Validates that all required fields are filled in.

    Parameters:
        fields (List[str]): A list of form fields to check for completion.

    Returns:
        bool: True if all fields are filled, False otherwise.
    """
    return all(fields)


def add_new_customer(customer_type: str, customer_data: dict) -> int:
    """
    Adds a new customer to the database based on the customer type and provided data.

    Parameters:
        customer_type (str): Type of customer (either "Individual" or "Business").
        customer_data (dict): Data for the customer.

    Returns:
        int: The customer ID if successfully added, None otherwise.
    """
    customer_id = add_customer(
        customer_type,
        customer_data["first_name"],
        customer_data["last_name"],
        customer_data["email"],
        customer_data["phone"],
        customer_data["street"],
        customer_data["city"],
        customer_data["state"],
        customer_data["postal_code"],
        customer_data.get("social_security_number"),
        customer_data.get("business_name"),
        customer_data.get("tax_id_number"),
        customer_data.get("primary_contact_name"),
        customer_data.get("primary_contact_title"),
    )

    return customer_id


def add_vehicle_page() -> None:
    """
    Renders the Add Vehicle page for inventory clerks to add new vehicles and associated customer details.

    Parameters:
        None

    Returns:
        None
    """
    st.markdown("<h4 style=text-align:center;>Add Vehicle</h4>", unsafe_allow_html=True)
    st.write("")
    st.write("")

    cols1, cols2 = st.columns([1, 1], gap="medium")

    with cols1:
        st.markdown(
            "<h5 style=text-align:center;>Vehicle Details</h5>", unsafe_allow_html=True
        )

        sub_col1, sub_col2 = st.columns([1, 1], gap="medium")

        with sub_col1:
            # Get today's date and time
            purchase_date = get_purchase_date()

            # Input fields for Vehicle details
            vin = st.text_input("Vehicle VIN *", max_chars=17)

            # Fetch vehicle data (types, manufacturers, colors)
            vehicle_data = fetch_vehicle_data()
            max_year = datetime.now().year + 1

            # Dropdowns for vehicle type, manufacturer, and color
            vehicle_type = st.selectbox("Vehicle Type *", vehicle_data["vehicle_types"])
            manufacturer = st.selectbox("Manufacturer *", vehicle_data["manufacturers"])
            color = st.multiselect("Color *", vehicle_data["colors"])
            fuel_type = st.selectbox(
                "Fuel Type *",
                [
                    "Gas",
                    "Diesel",
                    "Natural Gas",
                    "Hybrid",
                    "Plugin Hybrid",
                    "Battery",
                    "Fuel Cell",
                ],
            )
            year = st.number_input(
                "Year *", min_value=1980, max_value=max_year
            )  # 1886 is the year the first car was made

        with sub_col2:
            horsepower = st.number_input("Horsepower *", min_value=0)
            model = st.text_input("Model *")
            condition = st.selectbox(
                "Condition *", ["Excellent", "Very Good", "Good", "Fair"]
            )
            purchase_price = st.number_input("Purchase Price *")
            description = st.text_area("Description", max_chars=2054)

    with cols2:
        st.markdown(
            "<h5 style=text-align:center;>Customer Details</h5>", unsafe_allow_html=True
        )
        customer_names = lookup_customers()
        select_customer = st.selectbox(
            "Select Customer *",
            customer_names + ["Add New Customer"],
            placeholder="Choose customer",
            disabled=False,
            index=None,
        )
        customer_id = None

        if select_customer == "Add New Customer":
            with st.expander("Add Customer"):
                cus_col1, cus_col2 = st.columns([1, 1], gap="medium")
                with cus_col1:
                    customer_email = st.text_input("Email *")
                    customer_phone = st.text_input("Phone Number *")
                    address_street = st.text_input("Street Address *")
                    address_city = st.text_input("City *")
                    address_state = st.text_input("State *")

                with cus_col2:
                    address_postal_code = st.text_input("Postal Code *")
                    customer_type = st.selectbox(
                        "Customer Type *", ["Individual", "Business"]
                    )

                    if customer_type == "Individual":
                        first_name = st.text_input("First Name *")
                        last_name = st.text_input("Last Name *")
                        social_security_number = st.text_input(
                            "Social Security Number *"
                        )

                    else:  # Business
                        business_name = st.text_input("Business Name *")
                        tax_id_number = st.text_input("Tax Identification Number *")
                        primary_contact_name = st.text_input("Primary Contact Name *")
                        primary_contact_title = st.text_input("Primary Contact Title *")

                with cus_col1:
                    if st.button("Publish Customer"):
                        customer_data = {
                            "customer_type": customer_type,
                            "email": customer_email,
                            "phone": customer_phone,
                            "street": address_street,
                            "city": address_city,
                            "state": address_state,
                            "postal_code": address_postal_code,
                        }

                        if customer_type == "Individual":
                            customer_data.update(
                                {
                                    "first_name": first_name,
                                    "last_name": last_name,
                                    "social_security_number": social_security_number,
                                }
                            )
                        elif customer_type == "Business":
                            customer_data.update(
                                {
                                    "business_name": business_name,
                                    "tax_id_number": tax_id_number,
                                    "primary_contact_name": primary_contact_name,
                                    "primary_contact_title": primary_contact_title,
                                }
                            )

                        # Ensure all fields are filled
                        if all(customer_data.values()):
                            customer_id = add_new_customer(customer_type, customer_data)
                            if customer_id:
                                st.success("New customer added successfully!")
                                time.sleep(2)
                                st.rerun()
                        else:
                            st.error("Please fill in required fields.")
        else:
            if not select_customer:
                st.warning("Select customer first")
            else:
                customer_id = fetch_customer_id(select_customer)[0]

                if customer_id:
                    with cols1:
                        st.write("")
                        st.write("")

                        if st.button("Add Vehicle"):
                            required_fields = [
                                vin,
                                vehicle_type,
                                manufacturer,
                                model,
                                year,
                                condition,
                                fuel_type,
                                horsepower,
                                color,
                                purchase_price,
                                purchase_date,
                                select_customer,
                            ]

                            if all(required_fields):
                                success = add_vehicle_and_related_data(
                                    vin,
                                    vehicle_type,
                                    manufacturer,
                                    condition,
                                    model,
                                    year,
                                    fuel_type,
                                    horsepower,
                                    color,
                                    customer_id,
                                    st.session_state["username"],
                                    purchase_price,
                                    purchase_date,
                                    description if description else "",
                                )

                                if success:
                                    st.session_state["selected_vin"] = vin
                                    st.success("Vehicle added successfully!")
                                    st.switch_page(st.Page("pages/details.py"))
                                else:
                                    st.error(
                                        "Failed to add vehicle. Please check the details."
                                    )
                else:
                    st.error("Please fill in all required fields or select customer.")


# Call the function to render the page
add_vehicle_page()

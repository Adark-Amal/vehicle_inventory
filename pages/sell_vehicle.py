import streamlit as st
from controllers.extract_data import (
    lookup_customers,
    get_vehicle_details_for_sale,
    record_sale,
    fetch_customer_id,
)
from pages.add_vehicle import add_new_customer
from datetime import datetime
import pandas as pd
import time


def sell_vehicle_page() -> None:
    """
    Renders the Sell Vehicle page for salespeople to sell vehicles and record sales transactions.

    Parameters:
        None

    Returns:
        None
    """
    st.markdown(
        "<h4 style=text-align:center;>Sell Vehicle</h4>", unsafe_allow_html=True
    )
    st.write("")
    st.write("")

    user_role = st.session_state.get("role", "Public")

    if not st.session_state.get("selected_vin", None):
        st.warning("Select a car to sell")

    else:
        # Extract selected vehicle details
        vehicle_details = get_vehicle_details_for_sale(
            st.session_state.get("selected_vin")
        )

        if not vehicle_details:
            st.warning("No vehicle for sale.")
            return

        if user_role == "Owner":
            if not st.session_state.get("all_parts_installed", False):
                st.error(
                    "The vehicle cannot be sold because not all parts are installed."
                )
                return

        # Vehicle details section
        st.subheader("📋 General Vehicle Details")
        st.write("")
        sale_data = pd.DataFrame(
            vehicle_details.items(), columns=["Attributes", "Value"]
        )
        st.dataframe(sale_data, use_container_width=True, hide_index=True, height=495)

        st.markdown("-----")

        st.write("")
        st.subheader("📋 Buyer Details")
        st.write("")

        customer_names = lookup_customers()
        select_customer = st.selectbox(
            "Select Buyer *",
            customer_names + ["Add New Buyer"],
            placeholder="Choose buyer",
            index=None,
        )

        if select_customer == "Add New Buyer":
            with st.expander("Add Buyer"):
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

                if st.button("Publish Buyer"):
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

                    if all(customer_data.values()):
                        customer_id = add_new_customer(customer_type, customer_data)
                        if customer_id:
                            st.success("Buyer added successfully!")
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error("Failed to add buyer. Please try again.")
                    else:
                        st.error("Please fill in all required fields.")
        else:
            if not select_customer:
                st.warning("Select customer first")
            else:
                customer_id = fetch_customer_id(select_customer)[0]

                if customer_id:
                    st.write("")
                    st.write("")
                    if st.button("Confirm Sale", key="confirm_sale_button"):
                        if st.session_state.get("selected_vin") and select_customer:
                            success = record_sale(
                                vin=st.session_state.get("selected_vin"),
                                customer_identifier=customer_id,
                                sale_price=vehicle_details["SalePrice"],
                                sale_date=datetime.now(),
                                username=st.session_state["username"],
                            )

                            if success:
                                st.success(f"Vehicle sold to customer successfully!")
                                time.sleep(1)
                                st.rerun()
                                st.switch_page(st.Page("pages/details.py"))
                            else:
                                st.error("Failed to record sale. Please try again.")
                        else:
                            st.error("Please select a vehicle and buyer.")


# Call the function to render the page
sell_vehicle_page()

import streamlit as st
from db.session import create_session
from controllers.extract_data import (
    add_parts_order,
    add_vendor,
    get_vehicle_details_for_sale,
)
import time


def add_parts_order_page():
    """Renders the Add Parts Order page."""
    st.markdown(
        "<h4 style=text-align:center;>Add Parts Order</h4>", unsafe_allow_html=True
    )

    st.write("")
    st.write("")
    # Extract selected vehicle details
    vehicle_details = get_vehicle_details_for_sale(st.session_state.get("selected_vin"))
    if not vehicle_details:
        st.warning("Can't enter parts for sold vehicle.")
        return

    st.markdown("#### Enter Required Details")
    # Initialize session state variables if not already set
    if "vin" not in st.session_state:
        st.session_state["vin"] = ""
    if "num_parts" not in st.session_state:
        st.session_state["num_parts"] = 1
    if "forms_generated" not in st.session_state:
        st.session_state["forms_generated"] = False
    if "selected_vendor" not in st.session_state:
        st.session_state["selected_vendor"] = None

    # Initialize session state for vendor names if not initialized
    if "vendor_names" not in st.session_state:
        with create_session() as session:
            vendors = session.execute("SELECT name FROM Vendor").fetchall()
            st.session_state.vendor_names = [
                vendor[0] for vendor in vendors
            ]  # Extract vendor names

    vin1, vin2 = st.columns([1, 1], gap="medium")
    with vin1:
        vin = st.text_input(
            "Vehicle VIN *",
            max_chars=17,
            value=(
                None
                if "selected_vin" not in st.session_state
                else st.session_state["selected_vin"]
            ),
            placeholder="Enter VIN",
        )
    with vin2:
        selected_vendor = st.selectbox(
            f"Select Vendor *",
            st.session_state.vendor_names + ["Add New Vendor"],
            index=None,
            key=f"vendor_select",
            placeholder="Select vendor",
        )

        # Handle vendor selection logic
        if selected_vendor == "Add New Vendor":
            with st.expander("Add Vendor Details"):
                new_vendor_name = st.text_input(
                    "Vendor Name", key="new_vendor_name"
                ).strip()
                new_vendor_phone = st.text_input(
                    "Vendor Phone", key="new_vendor_phone"
                ).strip()
                new_vendor_address = st.text_input(
                    "Vendor Address", key="new_vendor_address"
                ).strip()
                new_vendor_city = st.text_input(
                    "Vendor City", key="new_vendor_city"
                ).strip()
                new_vendor_state = st.text_input(
                    "Vendor State", key="new_vendor_state"
                ).strip()
                new_vendor_postal_code = st.text_input(
                    "Vendor Postal Code", key="new_vendor_postal_code"
                ).strip()

                if st.button("Add Vendor"):
                    if all(
                        [
                            new_vendor_name,
                            new_vendor_phone,
                            new_vendor_address,
                            new_vendor_city,
                            new_vendor_state,
                            new_vendor_postal_code,
                        ]
                    ):
                        if add_vendor(
                            new_vendor_name,
                            new_vendor_phone,
                            new_vendor_address,
                            new_vendor_city,
                            new_vendor_state,
                            new_vendor_postal_code,
                        ):
                            st.success(
                                f"Vendor '{new_vendor_name}' added successfully!"
                            )
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Failed to add vendor. Vendor may already exist.")
                    else:
                        st.error("Please fill in all vendor details.")

    # Save VIN and selected vendor in session state
    if vin and vin.strip() and selected_vendor and selected_vendor != "Add New Vendor":
        st.session_state["vin"] = vin.strip()
        st.session_state["selected_vendor"] = selected_vendor

    if (
        not st.session_state["vin"]
        or not st.session_state["selected_vendor"]
        or selected_vendor == "Add New Vendor"
    ):
        st.warning("Please select a vendor or add VIN")

    else:
        st.write("")
        st.write("")
        st.markdown("---")
        st.markdown("#### Generate Parts Form")

        with st.form(key="input_form"):
            num_parts = st.number_input(
                "Number of Parts",
                min_value=1,
                max_value=100,
                step=1,
                value=st.session_state["num_parts"],
            )

            run_button = st.form_submit_button("➕ Add Parts")

        # When the "Generate Forms" button is clicked, generate the specified number of part forms
        if run_button:
            if not vin.strip():
                st.warning("Enter VIN first.")  # Show warning if VIN is empty
            elif not selected_vendor and selected_vendor == "Add New Vendor":
                st.warning("Select a vendor")
            else:
                new_num_parts = int(num_parts)
                st.session_state["forms_generated"] = True

                # Remove per-part session state variables if num_parts has decreased
                existing_parts = [
                    key for key in st.session_state.keys() if key.startswith("part_")
                ]
                for key in existing_parts:
                    idx = int(key.split("_")[1])
                    if idx >= new_num_parts:
                        del st.session_state[key]

                st.session_state["num_parts"] = new_num_parts

                # Initialize parts_list
                st.session_state.parts_list = [
                    {} for _ in range(st.session_state["num_parts"])
                ]

    # Render the part forms dynamically based on the session state
    if st.session_state.get("forms_generated", False):
        for idx in range(st.session_state["num_parts"]):
            st.markdown(f"### Part {idx + 1}")

            # Initialize default values if not in session state
            if f"part_{idx}" not in st.session_state:
                st.session_state[f"part_{idx}"] = {
                    "part_description": "",
                    "vendor_part_number": "",
                    "unit_price": 0.0,
                    "quantity": 1,
                    "part_status": "Ordered",
                }

            part = st.session_state[f"part_{idx}"]

            # Create two columns
            col1, col2 = st.columns(2)

            with col1:
                # First column widgets
                part_description = st.text_input(
                    f"Part Description {idx + 1}",
                    value=part["part_description"],
                    key=f"desc_{idx}",
                )
                unit_price = st.number_input(
                    f"Unit Price {idx + 1}",
                    min_value=0.0,
                    value=part["unit_price"],
                    format="%.2f",
                    key=f"price_{idx}",
                )
                quantity = st.number_input(
                    f"Quantity {idx + 1}",
                    min_value=1,
                    value=part["quantity"],
                    format="%d",
                    key=f"quantity_{idx}",
                )

            with col2:
                # Second column widgets
                part_status = st.selectbox(
                    f"Part Status {idx + 1}",
                    ["Ordered", "Received", "Installed"],
                    index=["Ordered", "Received", "Installed"].index(
                        part["part_status"]
                    ),
                    key=f"status_{idx}",
                )
                vendor_part_number = st.text_input(
                    f"Vendor Part Number {idx + 1}",
                    value=part["vendor_part_number"],
                    key=f"vendor_part_{idx}",
                )

            # Update the part in session state
            st.session_state[f"part_{idx}"] = {
                "part_description": part_description.strip(),
                "vendor_part_number": vendor_part_number.strip(),
                "unit_price": unit_price,
                "quantity": quantity,
                "part_status": part_status,
                "selected_vendor": selected_vendor,
            }

            # Add horizontal line after each part, except after the last one
            if idx < st.session_state["num_parts"] - 1:
                st.markdown("---")

        # Submit button
        if st.button("Submit Order"):
            vin = st.session_state.get("vin", "").strip()

            if not vin:
                st.error("VIN is required.")
            elif not selected_vendor:
                st.error("Vendor is required.")
            else:
                parts = []  # Collect all parts into a list
                all_parts_valid = True  # Flag to check if all parts have valid data

                for idx in range(st.session_state["num_parts"]):
                    part = st.session_state[f"part_{idx}"]
                    required_fields = [
                        part["part_description"],
                        part["unit_price"],
                        part["quantity"],
                        part["part_status"],
                        part["selected_vendor"],
                    ]

                    if (
                        not all(required_fields)
                        or part["unit_price"] <= 0
                        or part["quantity"] <= 0
                    ):
                        st.error(
                            f"Please fill in all required fields for Part {idx + 1}."
                        )
                        all_parts_valid = False
                        break

                    parts.append(part)

                if all_parts_valid:
                    success = add_parts_order(vin, part["selected_vendor"], parts)

                    if success:
                        st.success("Parts order added successfully!")

                        # Reset session state variables
                        st.session_state["forms_generated"] = False
                        st.session_state["num_parts"] = 1
                        st.session_state["parts_list"] = []
                        for key in list(st.session_state.keys()):
                            if key.startswith("part_"):
                                del st.session_state[key]

                        time.sleep(2)
                        st.rerun()  # Rerun the app to reset the form
                        st.switch_page(st.Page("pages/details.py"))
                    else:
                        st.error(
                            "Failed to add parts order. Make sure vendor part number is unique"
                        )


# Call the function to render the page
add_parts_order_page()

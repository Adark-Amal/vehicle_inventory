import streamlit as st
from controllers.extract_data import (
    get_vehicle_details_for_public,
    get_vehicle_parts,
    get_purchase_details,
    get_sale_details,
    update_status,
    get_vehicle_details,
)
from utils.constants import STATUS_ACCESS_ROLES, VEHICLE_STATUS_OPTIONS
import pandas as pd
import time


def vehicle_details_page():
    """
    Displays the vehicle details page with an image carousel at the top and car details below.
    Tailored content is shown based on the user's role.
    """

    # Define user role from session (for this example, using a placeholder role)
    user_role = st.session_state.get("role", "Public")

    if not st.session_state.get("selected_vin", None):
        st.warning("No vehicle selected")
    else:
        # Retrieve vehicle details
        vehicle_details = get_vehicle_details_for_public(
            st.session_state.get("selected_vin"), role=user_role
        )
        parts_data = get_vehicle_parts(st.session_state.get("selected_vin"))
        vehicle_sold_detail = get_vehicle_details(
            st.session_state.get("selected_vin"), role=user_role
        )
        # Vehicle details section
        st.subheader("📋 General Vehicle Details")
        st.write("")

        if user_role == "Salesperson":
            if vehicle_details.empty:
                st.warning("No vehicle details to view.")
                return
            else:
                st.dataframe(vehicle_details, use_container_width=True, hide_index=True)

                if st.button("🛒 Sell Vehicle"):
                    st.switch_page(st.Page("pages/sell_vehicle.py"))
        else:
            if user_role in ["Owner", "Manager", "Inventory clerk"]:
                if vehicle_details.empty:
                    st.warning("No vehicle details to view.")
                else:
                    st.dataframe(
                        vehicle_details, use_container_width=True, hide_index=True
                    )
            else:
                st.dataframe(vehicle_details, use_container_width=True, hide_index=True)

        if user_role in ["Manager", "Owner"]:
            st.write("")
            st.markdown("-----")
            st.subheader("🚘 Purchase Details")
            buyer_details = get_purchase_details(st.session_state["selected_vin"])

            if buyer_details:
                st.dataframe(
                    pd.DataFrame(buyer_details.items(), columns=["Attribute", "Value"]),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.warning(
                    f"No vehicle with VIN: {st.session_state['selected_vin']} in inventory"
                )
            st.write("")

            st.markdown("-----")
            st.subheader("🚗 Sale Details")
            seller_details = get_sale_details(st.session_state["selected_vin"])
            if seller_details:
                st.dataframe(
                    pd.DataFrame(
                        seller_details.items(), columns=["Attribute", "Value"]
                    ),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.warning(
                    f"Vehicle with VIN: {st.session_state['selected_vin']} has not been sold yet"
                )
            st.write("")

        st.write("")
        st.write("")

        # Role-based additional details
        if user_role in ["Inventory clerk", "Owner"]:
            st.markdown("-----")
            st.subheader("🔩 Parts Section")
            st.write("")

            if not parts_data:
                st.warning("Vehicle has no parts ordered, recieved or installed")
            # Display each part using the full column width
            for part in parts_data:

                # Create a dataframe for the part's details
                part_df = pd.DataFrame([part])

                # Display the dataframe using the full width
                st.dataframe(part_df, use_container_width=True, hide_index=True)

                # Status update functionality
                if part["PartStatus"] == "Ordered":
                    status_options = ["Received", "Installed"]
                elif part["PartStatus"] == "Received":
                    status_options = ["Installed"]
                else:
                    status_options = []

                # Show status options if available
                if status_options:
                    col = st.container()
                    with col:
                        selected_status_key = (
                            f"selected_status_{part['VendorPartNumber']}"
                        )
                        if selected_status_key not in st.session_state:
                            st.session_state[selected_status_key] = None

                        # Display radio buttons for status selection
                        selected_status = st.radio(
                            f"Update status for {part['VendorPartNumber']}:",
                            options=status_options,
                            index=(
                                status_options.index(
                                    st.session_state[selected_status_key]
                                )
                                if st.session_state[selected_status_key]
                                else 0
                            ),
                            key=f"radio_{part['VendorPartNumber']}",
                            label_visibility="hidden",
                        )

                        # Update the selected status in session state
                        st.session_state[selected_status_key] = selected_status

                        if st.button(
                            f"Update {part['VendorPartNumber']}",
                            key=f"update_status_{part['VendorPartNumber']}",
                        ):
                            if part["VendorPartNumber"] and part["OrderNumber"]:
                                success = update_status(
                                    selected_status,
                                    part["VendorPartNumber"],
                                    part["OrderNumber"],
                                )
                                if success:
                                    # Add logic for updating status and rerunning app
                                    st.success(
                                        f"Status updated to {selected_status} for {part['VendorPartNumber']}"
                                    )
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error(
                                        "Part order number or part number incorrect"
                                    )
                st.write("")
                st.write("")
                st.write("")
                st.markdown("-----")
            col1, col2, col3, col4 = st.columns([1, 1, 3, 3], gap="small")

            if user_role == "Owner":
                if not vehicle_sold_detail.empty:
                    st.session_state["all_parts_installed"] = (
                        all(part["PartStatus"] == "Installed" for part in parts_data)
                        if parts_data
                        else True
                    )
                    with col1:
                        # Button to add new parts order
                        if st.button("➕ Add Parts Order"):
                            st.switch_page(st.Page("pages/add_parts_order.py"))
                    with col2:
                        if (
                            st.session_state["all_parts_installed"]
                            and vehicle_details.to_records()[-1][-1] is None
                        ):
                            if st.button("🛒 Sell Vehicle"):
                                st.switch_page(st.Page("pages/sell_vehicle.py"))
                        # if st.button("🛒 Sell Vehicle"):
                        #    st.switch_page(st.Page("pages/sell_vehicle.py"))
            else:
                if not vehicle_sold_detail.empty:
                    # Button to add new parts order
                    if st.button("➕ Add Parts Order"):
                        st.switch_page(st.Page("pages/add_parts_order.py"))


vehicle_details_page()

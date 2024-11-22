import streamlit as st
from utils.auth import login, logout
from typing import Dict

# Set up the app title and layout
st.set_page_config(page_title="North Avenue Automobile", layout="wide")
st.logo("assets/icon.png")
st.html(
    """
  <style>
    [alt=Logo] {
        top: -10px; 
        height: 6rem;
        margin-bottom: -20px;
        margin-left: -20px;
    }
  </style>
        """
)

# Initialize session state for login status and username
st.session_state.setdefault("logged_in", False)
st.session_state.setdefault("username", "")
st.session_state.setdefault("show_reports", False)

# Define application pages
search_page = st.Page(
    "pages/search.py", title="Search", icon=":material/search:", default=True
)
login_page = st.Page(login, title="Log in", icon=":material/login:")
logout_page = st.Page(logout, title="Log out", icon=":material/logout:")
add_parts_page = st.Page(
    "pages/add_parts_order.py", title="Add Parts Order", icon=":material/extension:"
)
add_vehicle_page = st.Page(
    "pages/add_vehicle.py", title="Add Vehicle", icon=":material/directions_car:"
)
sell_vehicle_page = st.Page(
    "pages/sell_vehicle.py", title="Sell Vehicle", icon=":material/sell:"
)
details_page = st.Page(
    "pages/details.py", title="View Details", icon=":material/manage_search:"
)

# Define report pages
seller_history = st.Page(
    "pages/reports/seller_history.py",
    title="Seller History Report",
    icon=":material/timeline:",
)
avt = st.Page(
    "pages/reports/average_inventory_time.py",
    title="AVT Report",
    icon=":material/avg_time:",
)
ppc = st.Page(
    "pages/reports/price_per_condition.py",
    title="PPC Report",
    icon=":material/bar_chart:",
)
parts_statistics = st.Page(
    "pages/reports/parts_statistics.py",
    title="Parts Statistics Report",
    icon=":material/table_chart:",
)
monthly_sales = st.Page(
    "pages/reports/monthly_sales.py",
    title="Monthly Sales Report",
    icon=":material/chart_data:",
)


def show_sidebar_welcome() -> None:
    """
    Displays a welcome message in the sidebar for logged-in users.

    Parameters:
        None

    Returns:
        None
    """
    st.sidebar.write(f"**Welcome, {st.session_state['username']}!**")


def get_navigation_by_role(role: str) -> Dict[str, list]:
    """
    Returns the navigation structure based on the user's role.

    Parameters:
        role (str): The role of the logged-in user.

    Returns:
        dict: A dictionary representing navigation options.
    """
    common_pages = {"Tools": [search_page]}

    role_specific_pages = {
        "Inventory clerk": {
            "Role Action": [details_page, add_parts_page, add_vehicle_page]
        },
        "Salesperson": {"Role Action": [details_page, sell_vehicle_page]},
        "Manager": {"Role Action": [details_page]},
        "Owner": {
            "Role Action": [
                details_page,
                add_parts_page,
                add_vehicle_page,
                sell_vehicle_page,
            ]
        },
    }

    return {**common_pages, **role_specific_pages.get(role, {})}


def display_navigation() -> None:
    """
    Displays the navigation menu based on the user's login status and role.

    Parameters:
        None

    Returns:
        None
    """

    if st.session_state["logged_in"]:
        show_sidebar_welcome()
        user_role = st.session_state.get("role", "")
        navigation_structure = get_navigation_by_role(user_role)

        if st.session_state.get("show_reports", False):
            navigation_structure.update(
                {"Reports": [seller_history, avt, ppc, parts_statistics, monthly_sales]}
            )

        # Add "Account" as the last item in the navigation
        navigation_structure["Account"] = [logout_page]

    else:
        st.session_state["show_reports"] = False
        navigation_structure = {
            "Tools": [search_page],
            "Role Action": [details_page],
            "Account": [login_page],
        }

    # Get the current page from query parameters or default to search_page
    current_page = st.query_params.get("page", ["search"])[0]

    # Flatten the navigation structure to a list of pages
    all_pages = []
    for pages in navigation_structure.values():
        all_pages.extend(pages)

    # Map page titles to page objects
    page_dict = {page.title: page for page in all_pages}

    # If the current page is not in the navigation, reset to default
    if current_page not in page_dict:
        current_page = "Search"
        st.query_params.get(current_page, current_page)

    # Render navigation
    pg = st.navigation(navigation_structure)
    pg.run()


# Run the function to display the navigation
display_navigation()

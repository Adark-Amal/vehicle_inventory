from db.session import create_session
import streamlit as st
from typing import Optional, Dict
from utils.constants import VIN_ACCESS_ROLES, STATUS_ACCESS_ROLES


def initialize_session_states() -> None:
    """
    Initializes session state variables for login and search results.

    Parameters:
        None

    Returns:
        None
    """
    if "prev_logged_in" not in st.session_state:
        st.session_state["prev_logged_in"] = False
    if "search_results" not in st.session_state:
        st.session_state["search_results"] = None


def clear_search_results() -> None:
    """
    Clears the search results from the session state if they exist.

    Parameters:
        None

    Returns:
        None
    """
    if "search_results" in st.session_state:
        del st.session_state["search_results"]


def has_vin_access(role: str) -> bool:
    """
    Checks if a given role has access to VIN search.

    Parameters:
        role (str): The user's role.

    Returns:
        bool: True if the role has access to VIN search, False otherwise.
    """
    return role in VIN_ACCESS_ROLES


def has_status_access(role: str) -> bool:
    """
    Checks if a given role has access to vehicle status search.

    Parameters:
        role (str): The user's role.

    Returns:
        bool: True if the role has access to vehicle status search, False otherwise.
    """
    return role in STATUS_ACCESS_ROLES


def login_user(username: str, password: str) -> Optional[Dict[str, str]]:
    """
    Authenticates a user by checking the provided username and password.

    Parameters:
        username (str): The username entered by the user.
        password (str): The password entered by the user.

    Returns:
        Optional[Dict[str, str]]: A dictionary containing the user's username and role if authentication succeeds, otherwise None.
    """
    with create_session() as session:
        query = """
            SELECT username, role FROM User WHERE username = :username AND password = :password
        """
        result = session.execute(
            query, {"username": username, "password": password}
        ).fetchone()

        if result:
            return {"username": result[0], "role": result[1]}
        return None


def clear_session_state() -> None:
    """
    Clears all session state variables related to login.

    Parameters:
        None

    Returns:
        None
    """
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""
    st.session_state["role"] = "Public"


def logout_user() -> None:
    """
    Logs out the user by clearing session state variables.

    Parameters:
        None

    Returns:
        None
    """
    clear_session_state()


def get_user_role() -> Optional[str]:
    """
    Retrieves the role of the currently logged-in user.

    Parameters:
        None

    Returns:
        Optional[str]: The role of the logged-in user, or None if no user is logged in.
    """
    return st.session_state.get("role")


def login_form() -> Dict[str, Optional[str]]:
    """
    Displays the login form and captures username and password input.

    Parameters:
        None

    Returns:
        Dict[str, Optional[str]]: A dictionary containing the entered username, password, and the submit button state.
    """
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            st.header("Log In")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit_button = st.form_submit_button("Log in")
    return {"username": username, "password": password, "submit": submit_button}


def login() -> None:
    """
    Processes login and updates session state if authentication is successful.

    Parameters:
        None

    Returns:
        None
    """

    form_data = login_form()

    cols1, cols2, cols3 = st.columns([1, 2, 1])

    if form_data["submit"]:
        user = login_user(form_data["username"], form_data["password"])
        if user:
            st.session_state["logged_in"] = True
            st.session_state["username"] = user["username"]
            st.session_state["role"] = user["role"]
            st.rerun()
        else:
            with cols2:
                st.error("Invalid username or password")


def logout() -> None:
    """
    Logs out the user by clearing session state variables and refreshing the page.

    Parameters:
        None

    Returns:
        None
    """
    logout_user()
    st.rerun()

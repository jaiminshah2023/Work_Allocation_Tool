import streamlit as st
import pandas as pd
import re
import os
from Projects import handle_projects
from Tasks import handle_tasks
from Dashboard import show_dashboard, initialize_session
from datetime import datetime

# Import Google Sheets integration for user names
try:
    from google_sheets_integration import get_user_name_from_sheets, check_user_credentials, get_cached_data
    USE_GOOGLE_SHEETS = True
except ImportError:
    USE_GOOGLE_SHEETS = False
    st.error("Google Sheets integration is required but not available. Please check your configuration.")

st.set_page_config(layout="wide")

# === Session Initialization ===
if "is_logged_in" not in st.session_state:
    st.session_state["is_logged_in"] = False
if "user_email" not in st.session_state:
    st.session_state["user_email"] = ""
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "Tasks"
if "clear_task_filters" not in st.session_state:
    st.session_state["clear_task_filters"] = True

# === Email Validator ===
def validate_email(email):
    pattern = r"^[^\d][\w.-]*@(childhelpfoundationindia\.org|tigeranalytics\.com|skypathdigital\.com)$"
    return re.match(pattern, email)

# === Get User Name ===
def get_user_name(user_email):
    """Get user's name from Google Sheets credentials."""
    if USE_GOOGLE_SHEETS:
        return get_user_name_from_sheets(user_email)
    else:
        # Fallback to email prefix if Google Sheets not available
        return user_email.split('@')[0].capitalize()

# === Show Data Status ===
def show_data_status():
    """Show data freshness status in the sidebar."""
    if USE_GOOGLE_SHEETS:
        st.sidebar.markdown("**📊 Data Status**")
        
        # Check if we have cached data
        has_cached_data = False
        cache_keys = ['tasks', 'projects_list', 'projects_df', 'users']
        
        for key in cache_keys:
            if get_cached_data(key) is not None:
                has_cached_data = True
                break
        
        if has_cached_data:
            st.sidebar.success("🟢 Using cached data (faster)")
            st.sidebar.caption("Cache refreshes every 60 seconds")
        else:
            st.sidebar.info("🔵 Loading fresh data")
        
        st.sidebar.markdown("---")

# === Login Form ===
def login_form():
    st.title("🔐 Login")
    email = st.text_input("Enter your email")
    password = st.text_input("Enter password", type="password")

    if st.button("Login"):
        if USE_GOOGLE_SHEETS:
            # Check credentials using Google Sheets and password
            if check_user_credentials(email) and validate_email(email):
                if password == "Child#1234":
                    st.session_state["is_logged_in"] = True
                    st.session_state["user_email"] = email.strip()
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Incorrect password.")
            else:
                st.error("Invalid email or user not found in system.")
        else:
            st.error("Google Sheets integration is required for login. Please contact administrator.")

# === Sidebar ===
def sidebar():
    
    # Show data status first
    show_data_status()

    # Navigation buttons
    if st.sidebar.button("📝 Task Board", key="nav_tasks"):
        if st.session_state.current_page != "Tasks":
            st.session_state.clear_task_filters = True
        st.session_state.current_page = "Tasks"
        st.rerun()

    if st.sidebar.button("📂 Projects", key="nav_projects"):
        st.session_state.current_page = "Projects"
        st.rerun()

    if st.sidebar.button("📊 Projects Overview", key="nav_dashboard"):
        st.session_state.current_page = "Projects Overview"
        st.rerun()

    st.sidebar.markdown("---")
    
    # Cache Management Section
    st.sidebar.markdown("**🔄 Data Management**")
    if st.sidebar.button("🔄 Refresh Data", help="Clear cache to get latest data from Google Sheets"):
        if USE_GOOGLE_SHEETS:
            from google_sheets_integration import invalidate_cache
            invalidate_cache()  # Clear all cache
            st.sidebar.success("✅ Data cache cleared!")
            st.sidebar.info("💡 Page will refresh with latest data")
            st.rerun()
        else:
            st.sidebar.error("Google Sheets integration not available")
    
    st.sidebar.markdown("---")
    
    if st.sidebar.button("Logout", key="logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.success("Logged out.")
        st.rerun()

# === Main Pages ===
def tasks():
    # Get user's actual name from credentials
    user_name = get_user_name(st.session_state['user_email'])
    
    # Header with logos at the very top
    header_col1, header_col2, header_col3 = st.columns([1, 3, 1])
    
    with header_col1:
        if os.path.exists("logos/childlogo.jpg"):
            st.image("logos/childlogo.jpg", width=120)
        else:
            st.empty()
    
    with header_col2:
        st.markdown(
        f"<h2 style='text-align: center; margin-top: -20px;'>👋 Welcome, {user_name}</h2>",
        unsafe_allow_html=True
        )
    with header_col3:
        with st.container(horizontal=True, horizontal_alignment='right',vertical_alignment='center'):
            if os.path.exists("logos/tigerlogo.jpg"):
                st.image("logos/tigerlogo.jpg", width=120)
            else:
                st.empty()    
    st.markdown("---")  # Add separator line
    handle_tasks(st.session_state["user_email"])
    

def show_projects():
    handle_projects(st.session_state["user_email"])

# === Application Runner ===
def main():
    initialize_session()
    if not st.session_state["is_logged_in"]:
        login_form()
    else:
        sidebar()

        st.markdown("<br>", unsafe_allow_html=True)
        page = st.session_state["current_page"]

        if page == "Tasks":
            tasks()
        elif page == "Projects":
            show_projects()
        elif page == "Projects Overview":
            show_dashboard()

if __name__ == "__main__":
    main()

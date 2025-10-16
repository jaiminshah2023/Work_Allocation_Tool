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

    # Top logo row (before login form)
    st.markdown('')
    st.markdown('')
    logo_col1, logo_col2, logo_col3 = st.columns([1, 6, 1])

    with logo_col1:
        with st.container():
            st.image("logos/childlogo.jpg", width=120)
    with logo_col3:
        with st.container():
            st.image("logos/tigerlogo.jpg", width=120)

    # CSS fixes (with custom border styles added)
    st.markdown(
    """
    <style>
    [data-testid="column"] img {
        object-fit: contain;
        margin-top: 32px;
        height: auto !important;
        max-width: 120px !important;
    }

    .login-title {
        display: block;
        width: 100%;
        text-align: center;
        font-size: 36px;
        margin: 30px 0 25px 0;
        color: #2C3E50;
        font-weight: 700;
    }

    .input-label {
        font-size: 19px;
        font-weight: 550;
        color: #2C3E50;
        margin-bottom: 2px;
    }

    div.stTextInput > div {
        margin-top: -10px !important;
    }

    /* Center login button */
    div.stButton {
        display: flex;
        justify-content: center;
    }

    div.stButton > button {
        width: 120px;
        padding: 6px 0px !important;
        font-size: 14px !important;
        border-radius: 10px;
        background-color: #2C3E50;
        color: white;
        border: none;
        transition: 0.2s;
    }

    div.stButton > button:hover {
        background-color: #34495E;
        transform: scale(1.03);
    }

    div.stContainer > div:first-child {
        border: 10px solid #2C3E50;  /* Increased thickness */
        border-radius: 20px;         /* Rounded corners */
        padding: 25px;               /* Inner spacing so content doesn't touch border */
        box-shadow: 0 6px 15px rgba(0,0,0,0.2); /* Optional: subtle shadow */
    }

    </style>
    """,
    unsafe_allow_html=True
    )

    # Centered input fields and button
    col1, col2, col3 = st.columns([2, 3, 2])
    with col2:
        with st.container(border=True, horizontal_alignment='center', vertical_alignment='center'):
            st.markdown('<div class="login-title">Log-in</div>', unsafe_allow_html=True)
            st.markdown('<div class="input-label">✉️ Email</div>', unsafe_allow_html=True)
            email = st.text_input("", key="email", placeholder="Enter your email")
            st.markdown('<div class="input-label">🔑 Password</div>', unsafe_allow_html=True)
            password = st.text_input("", type="password", key="password", placeholder="Enter your password")
            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("Login", key="login_button"):
                if USE_GOOGLE_SHEETS:
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

# === Sidebar Navigation ===        
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

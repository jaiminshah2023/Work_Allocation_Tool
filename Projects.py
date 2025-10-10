import streamlit as st
import pandas as pd
import os
from datetime import date

# Import Google Sheets integration
try:
    from google_sheets_integration import (
        load_projects_df_from_sheets, save_projects_to_sheets, save_project_to_sheets,
        load_users_from_sheets, update_project_in_sheets
    )
    USE_GOOGLE_SHEETS = True
except ImportError:
    USE_GOOGLE_SHEETS = False
    st.error("Google Sheets integration is required but not available. Please check your configuration.")

# Remove local file references - all data now comes from Google Sheets

# === Load Users ===
def load_users():
    if USE_GOOGLE_SHEETS:
        return load_users_from_sheets()
    else:
        st.error("Google Sheets integration is required. Please contact administrator.")
        return []

# === Load Projects ===
def load_projects():
    if USE_GOOGLE_SHEETS:
        return load_projects_df_from_sheets()
    else:
        st.error("Google Sheets integration is required. Please contact administrator.")
        return pd.DataFrame(columns=[
            "project_name", "description", "start_date", "end_date", 
            "status", "priority", "created_by"
        ])

# === Save Project ===
def save_project(project):
    if USE_GOOGLE_SHEETS:
        return save_project_to_sheets(project)
    else:
        st.error("Google Sheets integration is required. Please contact administrator.")
        return False

# === Save Projects DataFrame ===
def save_projects_df(df):
    if USE_GOOGLE_SHEETS:
        return save_projects_to_sheets(df)
    else:
        st.error("Google Sheets integration is required. Please contact administrator.")
        return False

# === Handle Projects Page ===
def handle_projects(user_email):
    if user_email is None:
        user_email = st.session_state.get("email")

    if not user_email:
        st.warning("You must log in to access this page.")
        return

    # Header with logos for Projects page
    projects_header_col1, projects_header_col2, projects_header_col3 = st.columns([1, 3, 1])
    
    with projects_header_col1:
        if os.path.exists("logos/childlogo.jpg"):
            st.image("logos/childlogo.jpg", width=100)
        else:
            st.empty()
    
    with projects_header_col2:
        st.markdown("<h1 style='text-align: center; margin-top: 20px;'>📁 Projects</h1>", unsafe_allow_html=True)
    
    with projects_header_col3:
        if os.path.exists("logos/tigerlogo.jpg"):
            st.image("logos/tigerlogo.jpg", width=100)
        else:
            st.empty()
    
    st.markdown("---")  # Add separator line

    projects_df = load_projects()

    admin_emails = [
        "digital@childhelpfoundationindia.org",
        "rajendra.pathak@childhelpfoundationindia.org",
        "jiji.john@childhelpfoundationindia.org",
        "webteam@childhelpfoundationindia.org"
    ]
    col1, col2 = st.columns([1, 4])
    with col1:
        if user_email in admin_emails:
            if st.button("➕ Create New Project", key="create_project_btn"):
                st.session_state.show_create_form = True
        else:
            if st.button("➕ Create New Project", key="unauthorized_create_project_btn"):
                st.warning("Only authorized users can create projects.")

    # Removed warning confirmation step for creating new project

    if st.session_state.get("show_create_form") and (user_email in admin_emails):
        st.header("🆕 Create New Project")
        project_name = st.text_input("Project Name")
        description = st.text_area("Description")
        start_date = st.date_input("Start Date", date.today())
        start_date = pd.to_datetime(start_date).date()
        status = st.selectbox("Status", ["Not Started", "In Progress", "Completed"])
        priority = st.selectbox("Priority", ["Low", "Medium", "High"])
        created_by = user_email

        # End Date only enabled if status is Completed
        if status == "Completed":
            end_date = st.date_input("Project Completion Date", value=date.today())
            end_date = pd.to_datetime(end_date).date()
        else:
            st.text_input("Project Completion Date (set status to Completed to enable)", value="", disabled=True, key="disabled_proj_end_date")
            end_date = ""

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Save Project"):
                if not project_name:
                    st.error("Project name is required.")
                    return
                # If status is Completed, check for incomplete tasks
                if status == "Completed":
                    # Load tasks and check for incomplete tasks for this project
                    try:
                        from Tasks import load_tasks
                        tasks_df = load_tasks()
                        tasks_for_project = tasks_df[tasks_df['project_name'].astype(str).str.strip().str.lower() == project_name.strip().lower()]
                        incomplete_tasks = tasks_for_project[tasks_for_project['status'].isin(["Planned", "In Progress", "Blocked"])]
                        if not tasks_for_project.empty and not incomplete_tasks.empty:
                            st.error("Cannot complete project. There are tasks that are not completed (Planned, In Progress, or Blocked). Please complete all tasks before marking the project as completed.")
                            return
                    except Exception as e:
                        st.warning(f"Could not check tasks for project completion: {e}")
                save_project({
                    "project_name": project_name,
                    "description": description,
                    "start_date": start_date,
                    "end_date": end_date,
                    "status": status,
                    "priority": priority,
                    "created_by": created_by
                })
                st.success("Project saved successfully!")
                st.session_state.show_create_form = False
                st.rerun()
        with col2:
            if st.button("🔙 Back", key="back_create_project"):
                st.session_state.show_create_form = False
                st.rerun()

    # Sidebar: List project names
    with st.sidebar:
        st.subheader("🗂 Projects")
        for idx, row in projects_df.iterrows():
            # Ensure unique key by combining index and project name
            if st.button(row['project_name'], key=f"sidebar_proj_{idx}_{row['project_name']}"):
                st.session_state.selected_project_idx = idx
                st.session_state.show_project_detail = True
                st.session_state.show_edit_form = False
                st.rerun()

    # Project detail and edit logic
    if st.session_state.get("show_project_detail"):
        idx = st.session_state.get("selected_project_idx")
        project = projects_df.iloc[idx]
        st.header(f"📁 Project Detail: {project['project_name']}")
        st.markdown(f"**Description:** {project['description']}")
        st.markdown(f"**Start Date:** {project['start_date']}")
        st.markdown(f"**End Date:** {project['end_date']}")
        st.markdown(f"**Status:** {project['status']}")
        st.markdown(f"**Priority:** {project['priority']}")
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("✏️ Edit Project", key="edit_project_detail"):
                st.session_state.edit_project_idx = idx
                st.session_state.show_edit_form = True
                st.session_state.show_project_detail = False
                st.rerun()
        with col2:
            if st.button("🔙 Back", key="back_project_detail"):
                st.session_state.show_project_detail = False
                st.rerun()

    # Edit form for any user
    if st.session_state.get("show_edit_form"):
        idx = st.session_state.get("edit_project_idx")
        project = projects_df.iloc[idx]
        st.header(f"✏️ Edit Project: {project['project_name']}")
        project_name = st.text_input("Project Name", value=project['project_name'])
        description = st.text_area("Description", value=project['description'])
        start_date = st.date_input("Start Date", value=pd.to_datetime(project['start_date']).date() if pd.notna(project['start_date']) else date.today())
        start_date = pd.to_datetime(start_date).date()
        status = st.selectbox("Status", ["Not Started", "In Progress", "Completed"], index=["Not Started", "In Progress", "Completed"].index(project['status']))
        priority_options = ["Low", "Medium", "High"]
        priority_value = project['priority'] if project['priority'] in priority_options else "Low"
        priority = st.selectbox("Priority", priority_options, index=priority_options.index(priority_value))
        # End Date only enabled if status is Completed
        if status == "Completed":
            end_date = st.date_input("Project Completion Date", value=pd.to_datetime(project['end_date']).date() if pd.notna(project['end_date']) else date.today())
            end_date = pd.to_datetime(end_date).date()
        else:
            st.text_input("Project Completion Date (set status to Completed to enable)", value="", disabled=True, key="disabled_edit_proj_end_date")
            end_date = ""
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Save Changes", key="save_edit_project"):
                # If status is Completed, check for incomplete tasks
                if status == "Completed":
                    try:
                        from Tasks import load_tasks
                        tasks_df = load_tasks()
                        tasks_for_project = tasks_df[tasks_df['project_name'].astype(str).str.strip().str.lower() == project_name.strip().lower()]
                        incomplete_tasks = tasks_for_project[tasks_for_project['status'].isin(["Planned", "In Progress", "Blocked"])]
                        if not tasks_for_project.empty and not incomplete_tasks.empty:
                            st.error("Cannot complete project. There are tasks that are not completed (Planned, In Progress, or Blocked). Please complete all tasks before marking the project as completed.")
                            return
                    except Exception as e:
                        st.warning(f"Could not check tasks for project completion: {e}")
                # Update project using efficient update function
                updated_project = {
                    "project_name": project_name,
                    "description": description,
                    "start_date": start_date,
                    "end_date": end_date,
                    "status": status,
                    "priority": priority,
                    "created_by": project['created_by']  # Keep original creator
                }
                if update_project_in_sheets(project['project_name'], updated_project):
                    st.success("Project updated successfully!")
                    st.session_state.show_edit_form = False
                    st.session_state.show_project_detail = True
                    st.rerun()
                else:
                    st.error("Failed to update project. Please try again.")
        with col2:
            if st.button("🔙 Back", key="back_edit_project"):
                st.session_state.show_edit_form = False
                st.session_state.show_project_detail = True
                st.rerun()


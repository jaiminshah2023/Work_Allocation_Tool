import streamlit as st
import pandas as pd
import os
from datetime import date, datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Import Google Sheets integration
try:
    from google_sheets_integration import (
        load_tasks_from_sheets, save_tasks_to_sheets, load_users_from_sheets,
        get_user_name_from_sheets, load_projects_from_sheets, save_task_to_sheets,
        update_task_in_sheets
    )
    USE_GOOGLE_SHEETS = True
except ImportError:
    USE_GOOGLE_SHEETS = False
    st.error("Google Sheets integration is required but not available. Please check your configuration.")

# Remove local file references - all data now comes from Google Sheets

# === Load Tasks ===
def load_tasks():
    if USE_GOOGLE_SHEETS:
        return load_tasks_from_sheets()
    else:
        st.error("Google Sheets integration is required. Please contact administrator.")
        return pd.DataFrame(columns=[
            "task_name", "project_name", "assigned_to", "priority", "status",
            "start_date", "due_date", "completion_date", "comments", "created_by"
        ])

# === Save Task ===
def save_task(task):
    if USE_GOOGLE_SHEETS:
        return save_task_to_sheets(task)
    else:
        st.error("Google Sheets integration is required. Please contact administrator.")
        return False

# === Save DataFrame ===
def save_tasks_df(df):
    if USE_GOOGLE_SHEETS:
        return save_tasks_to_sheets(df)
    else:
        st.error("Google Sheets integration is required. Please contact administrator.")
        return False

# === Load Projects ===
def load_projects():
    if USE_GOOGLE_SHEETS:
        return load_projects_from_sheets()
    else:
        st.error("Google Sheets integration is required. Please contact administrator.")
        return []

# === Load Users ===
def load_users():
    if USE_GOOGLE_SHEETS:
        return load_users_from_sheets()
    else:
        st.error("Google Sheets integration is required. Please contact administrator.")
        return []

# === Get User Name ===
def get_user_name(user_email):
    if USE_GOOGLE_SHEETS:
        return get_user_name_from_sheets(user_email)
    else:
        # Fallback to email prefix if Google Sheets not available
        return user_email.split('@')[0].capitalize()

# === Handle Tasks Page ===
def handle_tasks(user_email):
    # Check authentication first
    if "is_logged_in" not in st.session_state or not st.session_state["is_logged_in"]:
        st.warning("You must log in to access this page.")
        return

    # Always load df and page at the start so they're available for all code paths
    page = st.session_state.get("task_page", "Tasks")
    df = load_tasks()
    df["assigned_to"] = df["assigned_to"].astype(str).str.strip().str.lower()
    user_email = user_email.strip().lower()

    if page == "NewTask":
        if user_email != "digital@childhelpfoundationindia.org":
            st.warning("Only authorized users can create tasks.")
            if st.button("🔙 Back"):
                st.session_state.task_page = "Tasks"
                st.rerun()
            return

        st.header("🆕 Create New Task")
        task_name = st.text_input("Task Name")
        description = st.text_area("Description")
        
        # Get projects list
        projects_list = load_projects()
        if not projects_list:
            st.error("No projects available. Please create a project first.")
            if st.button("🔙 Back", key="back_no_projects"):
                st.session_state.task_page = "Tasks"
                st.rerun()
            return
            
        project_name = st.selectbox("Project", projects_list)
        
        # Get users list
        users_list = load_users()
        if not users_list:
            st.error("No users available. Please check your user configuration.")
            return
            
        assigned_to = st.selectbox("Assign To", users_list)
        if assigned_to:
            assigned_to = assigned_to.strip().lower()
            
        priority = st.selectbox("Priority", ["Low", "Medium", "High"])
        status = st.selectbox("Status", ["Not Started", "In Progress", "Completed"])
        start = st.date_input("Start Date", date.today())
        start = pd.to_datetime(start).date()
        due = st.date_input("Due Date")
        due = pd.to_datetime(due).date()

        show_completion = status == "Completed"
        comp_date = None
        if show_completion:
            comp_date = st.date_input("Completion Date", value=date.today(), key="task_comp_date")
            comp_date = pd.to_datetime(comp_date).date()

        comments = st.text_area("Comments")

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Save Task", key="save_task"):
                if not task_name:
                    st.error("Task name is required.")
                    return
                if not assigned_to:
                    st.error("Please select a user to assign the task to.")
                    return
                
                # Prepare task data
                task_data = {
                    "task_name": task_name,
                    "description": description,
                    "project_name": project_name,
                    "assigned_to": assigned_to,
                    "priority": priority,
                    "status": status,
                    "start_date": start,
                    "due_date": due,
                    "completion_date": comp_date if show_completion else None,
                    "comments": comments,
                    "created_by": user_email
                }
                
                # Save task with error handling
                try:
                    if save_task(task_data):
                        st.success("Task saved successfully!")
                        st.session_state.task_page = "Tasks"
                        st.rerun()
                    else:
                        st.error("Failed to save task. Please try again.")
                except Exception as e:
                    st.error(f"Error saving task: {str(e)}")
                    
        with col2:
            if st.button("🔙 Back", key="back_task"):
                st.session_state.task_page = "Tasks"
                st.rerun()
        return

    # Header with logos for Tasks page
    tasks_header_col1, tasks_header_col2, tasks_header_col3 = st.columns([1, 3, 1])
    
    with tasks_header_col1:
        if os.path.exists("logos/childlogo.jpg"):
            st.image("logos/childlogo.jpg", width=100)
        else:
            st.empty()
    
    with tasks_header_col2:
        st.markdown("<h1 style='text-align: center; margin-top: 20px;'>📝 Tasks</h1>", unsafe_allow_html=True)
    
    with tasks_header_col3:
        if os.path.exists("logos/tigerlogo.jpg"):
            st.image("logos/tigerlogo.jpg", width=100)
        else:
            st.empty()
    
    st.markdown("---")  # Add separator line
    
    df = load_tasks()
    df["assigned_to"] = df["assigned_to"].astype(str).str.strip().str.lower()
    user_email = user_email.strip().lower()
    page = st.session_state.get("task_page", "Tasks")

    tab_today, tab_dashboard, tab_all, tab_my = st.tabs(["📅 Today's Tasks", "📊 Dashboard", "📋 All Tasks", "👤 My Tasks"])

    with tab_today:
        st.subheader("📅 Today's Tasks")
        
        # Show logged in user info
        user_name = get_user_name(user_email)
        st.info(f"👤 **Logged in as:** {user_name}")
        
        # Get today's date
        today = date.today()
        st.markdown(f"### Tasks scheduled for today: **{today.strftime('%B %d, %Y')}**")
        
        # Filter tasks for today and for the current user
        today_tasks = df[
            (df['assigned_to'] == user_email) & 
            (pd.to_datetime(df['start_date'], errors='coerce').dt.date == today)
        ].copy()
        
        if today_tasks.empty:
            st.info("🎉 No tasks scheduled for today! You're all caught up.")
            st.markdown("### 💡 What you can do:")
            st.markdown("- Check your **upcoming tasks** in the 'My Tasks' tab")
            st.markdown("- Review **overdue tasks** that need attention")
            st.markdown("- Plan ahead for tomorrow's schedule")
        else:
            # Show summary statistics for today
            total_today = len(today_tasks)
            completed_today = len(today_tasks[today_tasks['status'] == 'Completed'])
            in_progress_today = len(today_tasks[today_tasks['status'] == 'In Progress'])
            not_started_today = len(today_tasks[today_tasks['status'] == 'Not Started'])
            
            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📋 Total Tasks Today", total_today)
            with col2:
                st.metric("✅ Completed", completed_today)
            with col3:
                st.metric("🔄 In Progress", in_progress_today)
            with col4:
                st.metric("🆕 Not Started", not_started_today)
            
            st.markdown("---")
            
            # Group tasks by priority for better organization
            high_priority = today_tasks[today_tasks['priority'] == 'High']
            medium_priority = today_tasks[today_tasks['priority'] == 'Medium']
            low_priority = today_tasks[today_tasks['priority'] == 'Low']
            
            # Display high priority tasks first
            if not high_priority.empty:
                st.markdown("### 🔴 High Priority Tasks")
                for idx, row in high_priority.iterrows():
                    status_emoji = "✅" if row['status'] == 'Completed' else "🔄" if row['status'] == 'In Progress' else "🆕"
                    
                    with st.expander(f"{status_emoji} {row['task_name']}", expanded=row['status'] != 'Completed'):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"**Project:** {row['project_name']}")
                            st.write(f"**Description:** {row.get('description', 'No description')}")
                            st.write(f"**Due Date:** {pd.to_datetime(row['due_date']).strftime('%Y-%m-%d') if pd.notna(row['due_date']) else 'Not set'}")
                            st.write(f"**Status:** {row['status']}")
                            if row.get('comments'):
                                st.write(f"**Comments:** {row['comments']}")
                        with col2:
                            if st.button("Edit", key=f"edit_today_high_{idx}"):
                                st.session_state.edit_task_idx = idx
                                st.session_state.show_edit_dialog = True
                                st.session_state.active_tab = "today"
            
            # Display medium priority tasks
            if not medium_priority.empty:
                st.markdown("### 🟡 Medium Priority Tasks")
                for idx, row in medium_priority.iterrows():
                    status_emoji = "✅" if row['status'] == 'Completed' else "🔄" if row['status'] == 'In Progress' else "🆕"
                    
                    with st.expander(f"{status_emoji} {row['task_name']}", expanded=False):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"**Project:** {row['project_name']}")
                            st.write(f"**Description:** {row.get('description', 'No description')}")
                            st.write(f"**Due Date:** {pd.to_datetime(row['due_date']).strftime('%Y-%m-%d') if pd.notna(row['due_date']) else 'Not set'}")
                            st.write(f"**Status:** {row['status']}")
                            if row.get('comments'):
                                st.write(f"**Comments:** {row['comments']}")
                        with col2:
                            if st.button("Edit", key=f"edit_today_medium_{idx}"):
                                st.session_state.edit_task_idx = idx
                                st.session_state.show_edit_dialog = True
                                st.session_state.active_tab = "today"
            
            # Display low priority tasks
            if not low_priority.empty:
                st.markdown("### 🟢 Low Priority Tasks")
                for idx, row in low_priority.iterrows():
                    status_emoji = "✅" if row['status'] == 'Completed' else "🔄" if row['status'] == 'In Progress' else "🆕"
                    
                    with st.expander(f"{status_emoji} {row['task_name']}", expanded=False):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"**Project:** {row['project_name']}")
                            st.write(f"**Description:** {row.get('description', 'No description')}")
                            st.write(f"**Due Date:** {pd.to_datetime(row['due_date']).strftime('%Y-%m-%d') if pd.notna(row['due_date']) else 'Not set'}")
                            st.write(f"**Status:** {row['status']}")
                            if row.get('comments'):
                                st.write(f"**Comments:** {row['comments']}")
                        with col2:
                            if st.button("Edit", key=f"edit_today_low_{idx}"):
                                st.session_state.edit_task_idx = idx
                                st.session_state.show_edit_dialog = True
                                st.session_state.active_tab = "today"
            
            # Progress bar for today's completion
            if total_today > 0:
                completion_percentage = (completed_today / total_today) * 100
                st.markdown("---")
                st.markdown("### 📊 Today's Progress")
                st.progress(completion_percentage / 100)
                st.write(f"**{completion_percentage:.1f}%** of today's tasks completed ({completed_today}/{total_today})")

    with tab_dashboard:
        st.subheader("📊 Task Dashboard")
        
        # Show logged in user info
        user_name = get_user_name(user_email)
        st.info(f"👤 **Logged in as:** {user_name}")
        
        # Add filters for dashboard
        st.markdown("### 📊 Dashboard Filters")
        
        # Create filter columns
        filter_col1, filter_col2 = st.columns(2)
        filter_col3, filter_col4 = st.columns(2)
        
        with filter_col1:
            filter_project = st.multiselect(
                "Filter by Project",
                options=df['project_name'].unique().tolist() if not df.empty else [],
                default=df['project_name'].unique().tolist() if not df.empty else []
            )
        
        with filter_col2:
            filter_status = st.multiselect(
                "Filter by Status", 
                options=df['status'].unique().tolist() if not df.empty else [],
                default=df['status'].unique().tolist() if not df.empty else []
            )
        
        with filter_col3:
            filter_priority = st.multiselect(
                "Filter by Priority", 
                options=df['priority'].unique().tolist() if not df.empty and 'priority' in df.columns else [],
                default=df['priority'].unique().tolist() if not df.empty and 'priority' in df.columns else []
            )
        
        with filter_col4:
            filter_assignee = st.multiselect(
                "Filter by Assignee",
                options=df['assigned_to'].unique().tolist() if not df.empty else [],
                default=df['assigned_to'].unique().tolist() if not df.empty else []
            )
        
        # Apply filters
        df_filtered = df.copy()
        if not df_filtered.empty:
            if filter_project:
                df_filtered = df_filtered[df_filtered['project_name'].isin(filter_project)]
            if filter_status:
                df_filtered = df_filtered[df_filtered['status'].isin(filter_status)]
            if filter_priority and 'priority' in df_filtered.columns:
                df_filtered = df_filtered[df_filtered['priority'].isin(filter_priority)]
            if filter_assignee:
                df_filtered = df_filtered[df_filtered['assigned_to'].isin(filter_assignee)]
        
        # Calculate summary statistics with filtered data
        total_tasks = len(df_filtered) if not df_filtered.empty else 0
        completed_tasks = len(df_filtered[df_filtered['status'] == 'Completed']) if not df_filtered.empty else 0
        incomplete_tasks = len(df_filtered[df_filtered['status'] != 'Completed']) if not df_filtered.empty else 0
        
        # Calculate overdue tasks (tasks with due_date in the past and status != 'Completed')
        current_date = pd.Timestamp.now().date()
        overdue_tasks = 0
        if not df_filtered.empty and 'due_date' in df_filtered.columns:
            df_copy = df_filtered.copy()
            df_copy['due_date'] = pd.to_datetime(df_copy['due_date'], errors='coerce')
            overdue_mask = (
                (df_copy['due_date'].dt.date < current_date) & 
                (df_copy['status'] != 'Completed') &
                (df_copy['due_date'].notna())
            )
            overdue_tasks = len(df_copy[overdue_mask])
        
        # Display statistics in 4 columns
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Total completed tasks",
                value=str(completed_tasks)
            )
        
        with col2:
            st.metric(
                label="Total incomplete tasks", 
                value=str(incomplete_tasks)
            )
        
        with col3:
            st.metric(
                label="Total overdue tasks",
                value=str(overdue_tasks)
            )
        
        with col4:
            st.metric(
                label="Total tasks",
                value=str(total_tasks)
            )
        
        # Add some spacing
        st.markdown("---")
        
        if not df_filtered.empty:
            # Create charts in two rows
            
            # Row 1: Bar Chart and Project Distribution
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 Total Tasks by Status")
                # Bar chart for tasks by status
                status_counts = df_filtered['status'].value_counts().reset_index()
                status_counts.columns = ['Status', 'Task Count']
                
                fig_bar = px.bar(
                    status_counts, 
                    x='Status', 
                    y='Task Count',
                    title="Task Distribution by Status",
                    color='Status',
                    text='Task Count',
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig_bar.update_traces(texttemplate='%{text}', textposition='outside')
                fig_bar.update_layout(showlegend=False, height=400)
                st.plotly_chart(fig_bar, use_container_width=True)
            
            with col2:
                st.subheader("📁 Total Tasks by Project")
                # Bar chart for tasks by project
                project_counts = df_filtered['project_name'].value_counts().reset_index()
                project_counts.columns = ['Project', 'Task Count']
                
                fig_project = px.bar(
                    project_counts, 
                    x='Project', 
                    y='Task Count',
                    title="Task Distribution by Project",
                    color='Project',
                    text='Task Count',
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig_project.update_traces(texttemplate='%{text}', textposition='outside')
                fig_project.update_layout(
                    showlegend=False, 
                    height=400,
                    xaxis_tickangle=-45
                )
                st.plotly_chart(fig_project, use_container_width=True)
            
            # Row 2: Timeline and Pie Chart
            col3, col4 = st.columns(2)
            
            with col3:
                st.subheader("📈 Task Completion Over Time")
                # Prepare data for completion timeline
                df_timeline = df_filtered.copy()
                if 'completion_date' in df_timeline.columns:
                    df_timeline['completion_date'] = pd.to_datetime(df_timeline['completion_date'], errors='coerce')
                    completed_over_time = df_timeline[df_timeline['status'] == 'Completed'].copy()
                    
                    if not completed_over_time.empty:
                        # Group by completion date
                        completed_over_time['completion_date'] = completed_over_time['completion_date'].dt.date
                        timeline_data = completed_over_time.groupby('completion_date').size().reset_index()
                        timeline_data.columns = ['Date', 'Tasks Completed']
                        
                        # Create cumulative sum
                        timeline_data = timeline_data.sort_values('Date')
                        timeline_data['Cumulative Tasks'] = timeline_data['Tasks Completed'].cumsum()
                        
                        fig_timeline = px.line(
                            timeline_data, 
                            x='Date', 
                            y='Cumulative Tasks',
                            title="Cumulative Task Completion",
                            markers=True,
                            color_discrete_sequence=['#1f77b4']
                        )
                        fig_timeline.update_layout(
                            height=400,
                            xaxis=dict(
                                type='date',
                                tickformat='%Y-%m-%d'
                            )
                        )
                        st.plotly_chart(fig_timeline, use_container_width=True)
                    else:
                        st.info("No completed tasks with completion dates found.")
                else:
                    st.info("No completion date data available.")
            
            with col4:
                st.subheader("Task Completion Status This Month")
                # Pie chart for this month's completion status
                current_month_start = pd.Timestamp(datetime.now().replace(day=1))
                current_month_end = pd.Timestamp((datetime.now().replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1))

                # Filter tasks for current month (by due date or completion date)
                df_month = df_filtered.copy()
                df_month['due_date'] = pd.to_datetime(df_month['due_date'], errors='coerce')
                df_month['completion_date'] = pd.to_datetime(df_month['completion_date'], errors='coerce')

                # Tasks due this month or completed this month
                this_month_tasks = df_month[
                    ((df_month['due_date'] >= current_month_start) & 
                     (df_month['due_date'] <= current_month_end)) |
                    ((df_month['completion_date'] >= current_month_start) & 
                     (df_month['completion_date'] <= current_month_end))
                ]
                
                if not this_month_tasks.empty:
                    month_status_counts = this_month_tasks['status'].value_counts().reset_index()
                    month_status_counts.columns = ['Status', 'Count']
                    
                    fig_pie = px.pie(
                        month_status_counts, 
                        values='Count', 
                        names='Status',
                        title="Task Status Distribution (This Month)",
                        color_discrete_sequence=px.colors.qualitative.Set2
                    )
                    fig_pie.update_layout(height=400)
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.info("No tasks found for this month.")
        
        else:
            st.info("No tasks match the current filters. Please adjust your filter selections.")
            st.markdown("### 🔍 Current Filters:")
            st.write(f"- **Projects:** {filter_project if filter_project else 'All'}")
            st.write(f"- **Status:** {filter_status if filter_status else 'All'}")
            st.write(f"- **Priority:** {filter_priority if filter_priority else 'All'}")
            st.write(f"- **Assignees:** {filter_assignee if filter_assignee else 'All'}")

    with tab_all:
        st.subheader("📋 All Tasks")
        # Show filters horizontally at the top, matching Dashboard style
        filter_col1, filter_col2 = st.columns(2)
        filter_col3, filter_col4 = st.columns(2)
        with filter_col1:
            selected_project = st.multiselect(
                "Filter by Project",
                options=sorted(df['project_name'].dropna().unique().tolist()),
                default=sorted(df['project_name'].dropna().unique().tolist()),
                key="all_tasks_project_filter"
            )
        with filter_col2:
            selected_status = st.multiselect(
                "Filter by Status",
                options=sorted(df['status'].dropna().unique().tolist()),
                default=sorted(df['status'].dropna().unique().tolist()),
                key="all_tasks_status_filter"
            )
        with filter_col3:
            selected_priority = st.multiselect(
                "Filter by Priority",
                options=sorted(df['priority'].dropna().unique().tolist()) if 'priority' in df.columns else [],
                default=sorted(df['priority'].dropna().unique().tolist()) if 'priority' in df.columns else [],
                key="all_tasks_priority_filter"
            )
        with filter_col4:
            selected_assignee = st.multiselect(
                "Filter by Assignee",
                options=sorted(df['assigned_to'].dropna().unique().tolist()),
                default=sorted(df['assigned_to'].dropna().unique().tolist()),
                key="all_tasks_assignee_filter"
            )

        # Apply filters to All Tasks table
        filtered_df = df.copy()
        if selected_project:
            filtered_df = filtered_df[filtered_df['project_name'].isin(selected_project)]
        if selected_status:
            filtered_df = filtered_df[filtered_df['status'].isin(selected_status)]
        if selected_priority and 'priority' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['priority'].isin(selected_priority)]
        if selected_assignee:
            filtered_df = filtered_df[filtered_df['assigned_to'].isin(selected_assignee)]

        # Show Create New Task button below filters
        if user_email == "digital@childhelpfoundationindia.org":
            if st.button("+ Create New Task", key="create_new_task_btn"):
                st.session_state.show_create_task_warning = True
        else:
            if st.button("+ Create New Task", key="unauthorized_create_task_btn"):
                pass

        # Show filtered table data
        if filtered_df.empty:
            st.info("No tasks available for the selected filters.")
            st.markdown("### 🔍 Current Filters:")
            st.write(f"- **Projects:** {selected_project if selected_project else 'All'}")
            st.write(f"- **Status:** {selected_status if selected_status else 'All'}")
            st.write(f"- **Priority:** {selected_priority if selected_priority else 'All'}")
            st.write(f"- **Assignees:** {selected_assignee if selected_assignee else 'All'}")
        else:
            display_df = filtered_df.rename(columns={
                "task_name": "Task Name",
                "description": "Description",
                "project_name": "Project",
                "assigned_to": "Assignee",
                "priority": "Priority",
                "status": "Status",
                "start_date": "Start Date",
                "due_date": "Due Date",
                "completion_date": "Completion Date",
                "comments": "Comments",
                "created_by": "Created By"
            })[[
                "Task Name", "Description", "Project", "Assignee", "Priority", "Status", "Start Date", "Due Date", "Completion Date", "Comments", "Created By"
            ]]
            # Format all date columns to string YYYY-MM-DD
            for col in ["Start Date", "Due Date", "Completion Date"]:
                if col in display_df.columns:
                    display_df[col] = display_df[col].apply(lambda x: x.strftime("%Y-%m-%d") if pd.notna(x) and x != "" else "")
            st.dataframe(display_df, use_container_width=True)

        # Confirmation dialog for authorized user
        if st.session_state.get("show_create_task_warning"):
            if user_email == "digital@childhelpfoundationindia.org":
                st.warning("Are you sure you want to create a new task?")
                confirm_col, cancel_col = st.columns(2)
                with confirm_col:
                    if st.button("✅ Yes, proceed", key="confirm_create_task"):
                        st.session_state.task_page = "NewTask"
                        st.session_state.show_create_task_warning = False
                        st.rerun()
                with cancel_col:
                    if st.button("❌ Cancel", key="cancel_create_task_all"):
                        st.session_state.show_create_task_warning = False
                        st.rerun()
            else:
                st.warning("Only authorized users can create tasks. Please reach out to the project lead.")
                if st.button("❌ Close", key="close_unauthorized_task_all"):
                    st.session_state.show_create_task_warning = False
                    st.rerun()

    with tab_my:
        st.subheader("👤 My Tasks")
        st.write("Logged in as:", user_email)
        my_tasks = df[df['assigned_to'] == user_email]

        if my_tasks.empty:
            st.info("You have no assigned tasks.")
        else:
            st.markdown("### Your Assigned Tasks")
            for idx, row in my_tasks.iterrows():
                # Display each task in a single-row table
                task_display = pd.DataFrame([{
                    "Task Name": row.get("task_name", ""),
                    "Description": row.get("description", ""),
                    "Project": row.get("project_name", ""),
                    "Assign Date": row.get("start_date", ""),
                    "Due Date": row.get("due_date", ""),
                    "Priority": row.get("priority", ""),
                    "Status": row.get("status", ""),
                    "Completion Date": row.get("completion_date", "")
                }])
                # Format all date columns to string YYYY-MM-DD
                for col in ["Assign Date", "Due Date", "Completion Date"]:
                    if col in task_display.columns:
                        task_display[col] = task_display[col].apply(lambda x: x.strftime("%Y-%m-%d") if pd.notna(x) and x != "" else "")
                cols = st.columns([10, 1])
                with cols[0]:
                    st.dataframe(task_display, use_container_width=True, hide_index=True)
                with cols[1]:
                    if st.button("Edit", key=f"edit_my_task_{idx}"):
                        st.session_state.edit_task_idx = idx
                        st.session_state.show_edit_dialog = True
                        st.session_state.active_tab = "my"

    with st.sidebar:
        st.subheader("🗂 Tasks")
        
        # Show user info in sidebar
        user_name = get_user_name(user_email)
        st.markdown(f"**👤 {user_name}**")
        st.caption(f"📧 {user_email}")
        st.markdown("---")
        
        # Only show tasks assigned to the logged-in user in sidebar
        for task_name in df[df['assigned_to'] == user_email]['task_name'].unique():
            if st.button(task_name, key=f"task_sidebar_{task_name}"):
                st.session_state.selected_task = task_name
                st.session_state.task_page = "TaskDetail"
                st.rerun()

    # Shared Edit dialog logic for both Today's Tasks and My Tasks
    if st.session_state.get("show_edit_dialog") and st.session_state.get("edit_task_idx") is not None:
        # Determine which dataset to use based on active tab
        active_tab = st.session_state.get("active_tab", "my")
        if active_tab == "today":
            # Get today's tasks for the user
            today = date.today()
            today_tasks = df[
                (df['assigned_to'] == user_email) & 
                (pd.to_datetime(df['start_date'], errors='coerce').dt.date == today)
            ].copy()
            edit_tasks_df = today_tasks
        else:
            # Default to my tasks
            edit_tasks_df = df[df['assigned_to'] == user_email]
            
        if not edit_tasks_df.empty:
            edit_idx = st.session_state.edit_task_idx
            # Find the task in the edit_tasks_df by index
            if edit_idx in edit_tasks_df.index:
                edit_row = edit_tasks_df.loc[edit_idx]
                st.markdown("---")
                st.markdown("#### Edit Task")
                with st.form(key=f"edit_task_form_{edit_idx}", clear_on_submit=False):
                    new_task_name = st.text_input("Task Name", value=edit_row.get("task_name", ""))
                    new_description = st.text_area("Description", value=edit_row.get("description", ""))
                    new_due_date = st.date_input("Due Date", value=pd.to_datetime(edit_row.get("due_date", date.today())).date() if pd.notna(edit_row.get("due_date")) else date.today())
                    new_due_date = pd.to_datetime(new_due_date).date()
                    new_priority = st.selectbox("Priority", ["Low", "Medium", "High"], index=["Low", "Medium", "High"].index(edit_row.get("priority", "Medium")))
                    new_status = st.selectbox("Status", ["Not Started", "In Progress", "Completed"], index=["Not Started", "In Progress", "Completed"].index(edit_row.get("status", "Not Started")))
                    new_project = st.selectbox("Project", load_projects(), index=load_projects().index(edit_row.get("project_name", "")) if edit_row.get("project_name", "") in load_projects() else 0)
                    # Note: assigned_to and created_by are kept as original, not editable
                    new_start_date = st.date_input("Start Date", value=pd.to_datetime(edit_row.get("start_date", date.today())).date() if pd.notna(edit_row.get("start_date")) else date.today())
                    new_start_date = pd.to_datetime(new_start_date).date()
                    
                    # Completion Date - only show if status is Completed
                    show_completion = new_status == "Completed"
                    if show_completion:
                        new_completion_date = st.date_input("Completion Date", value=pd.to_datetime(edit_row.get("completion_date", date.today())).date() if pd.notna(edit_row.get("completion_date")) else date.today())
                        new_completion_date = pd.to_datetime(new_completion_date).date()
                    else:
                        new_completion_date = None
                    
                    new_comments = st.text_area("Comments", value=edit_row.get("comments", ""))
                    
                    submitted = st.form_submit_button("Save Changes")
                    cancel = st.form_submit_button("Cancel")
                    if submitted:
                        # Create updated task object
                        updated_task = {
                            "task_name": new_task_name,
                            "description": new_description,
                            "project_name": new_project,
                            "priority": new_priority,
                            "status": new_status,
                            "start_date": new_start_date,
                            "due_date": new_due_date,
                            "completion_date": new_completion_date if show_completion else None,
                            "comments": new_comments,
                            "assigned_to": edit_row.get("assigned_to"),  # Keep original assignee
                            "created_by": edit_row.get("created_by")     # Keep original creator
                        }
                        
                        # Use efficient update function
                        if update_task_in_sheets(edit_row.get("task_name"), updated_task):
                            st.success(f"Task '{new_task_name}' updated successfully!")
                            st.session_state.show_edit_dialog = False
                            st.session_state.edit_task_idx = None
                            st.session_state.active_tab = None
                            st.rerun()
                        else:
                            st.error("Failed to update task. Please try again.")
                    if cancel:
                        st.session_state.show_edit_dialog = False
                        st.session_state.edit_task_idx = None
                        st.session_state.active_tab = None
                        st.rerun()
            else:
                st.error("Task not found for editing.")
                st.session_state.show_edit_dialog = False
                st.session_state.edit_task_idx = None

# === Dashboard.py ===
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from datetime import date, datetime, timedelta

# Import Google Sheets integration
try:
    from google_sheets_integration import load_tasks_from_sheets
    USE_GOOGLE_SHEETS = True
except ImportError:
    USE_GOOGLE_SHEETS = False
    st.error("Google Sheets integration is required but not available. Please check your configuration.")

# Remove local file references - all data now comes from Google Sheets

# === Initialize Session ===
def initialize_session():
    if 'is_logged_in' not in st.session_state:
        st.session_state.is_logged_in = False
        st.session_state.user_email = ''
        st.session_state.page = 'Home'
        st.session_state.selected_project = None
        st.session_state.selected_task = None

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

# === Show Dashboard ===
def show_dashboard():
    st.markdown(
    "<h2 style='text-align: center; margin-top: 20px;'>📊 Dashboard</h2>",
    unsafe_allow_html=True
    )
    
    # Load data
    df = load_tasks()
    if not df.empty:
        df["assigned_to"] = df["assigned_to"].astype(str).str.strip().str.lower()
    
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
    
    # Check if any filters are active
    filters_active = (
        len(filter_project) < len(df['project_name'].unique().tolist() if not df.empty else []) or
        len(filter_status) < len(df['status'].unique().tolist() if not df.empty else []) or
        len(filter_priority) < len(df['priority'].unique().tolist() if not df.empty and 'priority' in df.columns else []) or
        len(filter_assignee) < len(df['assigned_to'].unique().tolist() if not df.empty else [])
    )
    
    # Display statistics in 4 columns
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        with st.container(border=True):
           
             
        
             st.metric(
            label="Total completed tasks",
            value=str(completed_tasks)
            )
    
    with col2:
        with st.container(border=True):
           st.metric(
            label="Total incomplete tasks", 
            value=str(incomplete_tasks)
           )
    
    with col3:
        with st.container(border=True):

            st.metric(
            label="Total overdue tasks",
            value=str(overdue_tasks)
            )
    
    with col4:
        with st.container(border=True):
            st.metric(
            label="Total tasks",
            value=str(total_tasks)
            )
    
    # Add some spacing
    st.markdown("---")
    
    if not df_filtered.empty:
        # Create charts in two rows
        
        # Row 1: Projects by Project Status (Doughnut) and Incomplete Tasks by Project (Bar)
        col1, col2 = st.columns(2)
        
        with col1:
             with st.container(border=True):
                  
                 
                #   st.subheader("📊 Projects by Project Status")
                  st.markdown(
                "<h5 style='font-size:25px; color:#333;'>📊 Projects by Project Status</h5>",
                unsafe_allow_html=True
                )
            # Doughnut chart for projects by status
                  if 'project_name' in df_filtered.columns and 'status' in df_filtered.columns:
                # Group projects by their overall status
                    def get_project_status(x):
                        if all(x == 'Completed'):
                                 return 'Completed'
                        elif all(x == 'Not Started'):
                                 return 'Not Started'
                        else:
                                 return 'In Progress'
                    project_status = df_filtered.groupby('project_name')['status'].apply(get_project_status).reset_index()
                    project_status.columns = ['Project', 'Project Status']

                # Ensure all status types are present
                    all_status_types = ['Not Started', 'In Progress', 'Completed']
                    project_status_counts = project_status['Project Status'].value_counts().reindex(all_status_types, fill_value=0).reset_index()
                    project_status_counts.columns = ['Status', 'Project Count']

                    fig_doughnut = px.pie(
                    project_status_counts,
                    values='Project Count',
                    names='Status',
                    # title="Projects by Project Status",
                    hole=0.4,  # This makes it a doughnut chart
                    color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    fig_doughnut.update_layout(height=400)
                    st.plotly_chart(fig_doughnut, use_container_width=True)
                  else:
                       st.info("No project data available for status analysis.")
        
        with col2:
             with st.container(border=True):
                st.markdown(
                "<h5 style='font-size:25px; color:#333;'>📈 Incomplete Tasks by Project</h5>",
                unsafe_allow_html=True
                )
               
            # Bar chart for incomplete tasks by project
                incomplete_tasks_data = df_filtered[df_filtered['status'] != 'Completed']
                if not incomplete_tasks_data.empty:

                    incomplete_counts = incomplete_tasks_data['project_name'].value_counts().reset_index()
                    incomplete_counts.columns = ['Project', 'Incomplete Tasks']
                
                    fig_incomplete = px.bar(
                    incomplete_counts,
                    x='Project',
                    y='Incomplete Tasks',
                    # title="Incomplete Tasks by Project",
                    color='Incomplete Tasks',
                    text='Incomplete Tasks',
                    color_continuous_scale='Reds'
                    )
                    fig_incomplete.update_traces(texttemplate='%{text}', textposition='outside')
                    fig_incomplete.update_layout(
                    height=400,
                    xaxis_tickangle=-45,
                    showlegend=False
                    )
                    st.plotly_chart(fig_incomplete, use_container_width=True)
                else:
                    st.info("No incomplete tasks found.")
        
        # Row 2: Only show Tasks by Assignee and Status (remove Completion Timeline)
        col3, _ = st.columns(2)
        with col3:
            with st.container(border=True):
                st.markdown(
                "<h5 style='font-size:25px; color:#333;'>👥 Total Tasks by Assignee and Task Status</h5>",
                unsafe_allow_html=True
                )

                
            # Stacked bar chart for tasks by assignee and status
                if not df_filtered.empty:

                    assignee_status = df_filtered.groupby(['assigned_to', 'status']).size().reset_index(name='Task Count')
                    fig_assignee = px.bar(
                    assignee_status,
                    x='assigned_to',
                    y='Task Count',
                    color='status',
                    # title="Tasks by Assignee and Status",
                    text='Task Count',
                    color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    fig_assignee.update_traces(texttemplate='%{text}', textposition='inside')
                    fig_assignee.update_layout(
                    height=400,
                    xaxis_tickangle=-45,
                    xaxis_title="Assignee",
                    yaxis_title="Task Count",
                    legend_title="Status"
                    )
                    st.plotly_chart(fig_assignee, use_container_width=True)
                else:
                    st.info("No task assignment data available.")
        # --- Daily basis tasks chart ---
        st.markdown("---")
        st.markdown(
                "<h5 style='font-size:25px; color:#333;'>📅 Daily Basis Tasks</h5>",
                unsafe_allow_html=True
        )
        if not df_filtered.empty and 'start_date' in df_filtered.columns:
            df_daily = df_filtered.copy()
            df_daily['start_date'] = pd.to_datetime(df_daily['start_date'], errors='coerce')
            daily_counts = df_daily.groupby(df_daily['start_date'].dt.date).size().reset_index(name='Tasks')
            fig_daily = px.bar(
                daily_counts,
                x='start_date',
                y='Tasks',
                # title="Tasks Created Per Day",
                text='Tasks',
                color='Tasks',
                color_continuous_scale='Blues'
            )
            fig_daily.update_traces(texttemplate='%{text}', textposition='outside')
            fig_daily.update_layout(height=400, xaxis_title="Date", yaxis_title="Number of Tasks", showlegend=False)
            st.plotly_chart(fig_daily, use_container_width=True)
        else:
            st.info("No start date data available for daily tasks chart.")

        # --- Days taken to complete each task chart ---
        st.markdown("---")
        st.markdown(
                "<h5 style='font-size:25px; color:#333;'>⏳Days Taken to Complete Each Task</h5>",
                unsafe_allow_html=True
        )
        if not df_filtered.empty and 'start_date' in df_filtered.columns and 'completion_date' in df_filtered.columns:
            df_days = df_filtered.copy()
            df_days['start_date'] = pd.to_datetime(df_days['start_date'], errors='coerce')
            df_days['completion_date'] = pd.to_datetime(df_days['completion_date'], errors='coerce')
            # Only consider tasks that are completed and have valid dates
            completed_mask = (df_days['status'] == 'Completed') & df_days['start_date'].notna() & df_days['completion_date'].notna()
            df_days_completed = df_days[completed_mask].copy()
            df_days_completed['days_taken'] = (df_days_completed['completion_date'] - df_days_completed['start_date']).dt.days
            if not df_days_completed.empty:
                fig_days = px.bar(
                    df_days_completed,
                    x='task_name',
                    y='days_taken',
                    # title="Days Taken to Complete Each Task",
                    text='days_taken',
                    color='days_taken',
                    color_continuous_scale='Viridis'
                )
                fig_days.update_traces(texttemplate='%{text}', textposition='outside')
                fig_days.update_layout(height=400, xaxis_title="Task Name", yaxis_title="Days Taken", showlegend=False)
                st.plotly_chart(fig_days, use_container_width=True)
            else:
                st.info("No completed tasks with valid dates for days taken chart.")
        else:
            st.info("Insufficient data for days taken to complete each task chart.")
    
    else:
        st.info("No tasks match the current filters. Please adjust your filter selections.")
        st.markdown("### 🔍 Current Filters:")
        st.write(f"- **Projects:** {filter_project if filter_project else 'All'}")
        st.write(f"- **Status:** {filter_status if filter_status else 'All'}")
        st.write(f"- **Priority:** {filter_priority if filter_priority else 'All'}")
        st.write(f"- **Assignees:** {filter_assignee if filter_assignee else 'All'}")

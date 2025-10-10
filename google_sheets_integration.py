# Google Sheets Integration for Work Allocation Tool
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import json
import time
from datetime import datetime, timedelta
import random
from gspread.exceptions import APIError

# === Rate Limiting and Caching ===
# Cache configuration
CACHE_DURATION_SECONDS = 60  # Cache data for 60 seconds
last_cache_time = {}
cached_data = {}

# Rate limiting configuration
API_CALL_DELAY = 1.2  # Delay between API calls in seconds
last_api_call_time = 0

# Toggle this to True only when you want verbose debug output in the Streamlit UI
# Set to False for normal operation to avoid showing debug popups to users
DEBUG = False

def rate_limit_api_call():
    """Add delay between API calls to respect rate limits."""
    global last_api_call_time
    current_time = time.time()
    time_since_last_call = current_time - last_api_call_time
    
    if time_since_last_call < API_CALL_DELAY:
        sleep_time = API_CALL_DELAY - time_since_last_call
        time.sleep(sleep_time)
    
    last_api_call_time = time.time()

def get_cached_data(cache_key):
    """Get data from cache if it's still valid."""
    if cache_key in cached_data and cache_key in last_cache_time:
        cache_age = datetime.now() - last_cache_time[cache_key]
        if cache_age.total_seconds() < CACHE_DURATION_SECONDS:
            return cached_data[cache_key]
    return None

def set_cached_data(cache_key, data):
    """Store data in cache with timestamp."""
    cached_data[cache_key] = data
    last_cache_time[cache_key] = datetime.now()

def invalidate_cache(cache_key=None):
    """Invalidate cache for specific key or all cache."""
    global cached_data, last_cache_time
    if cache_key:
        if cache_key in cached_data:
            del cached_data[cache_key]
        if cache_key in last_cache_time:
            del last_cache_time[cache_key]
    else:
        # Clear all cache
        cached_data.clear()
        last_cache_time.clear()

# === Google Sheets Configuration ===
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Get Google Sheets IDs from Streamlit secrets
def get_sheet_ids():
    """Get sheet IDs from Streamlit secrets."""
    try:
        return {
            'tasks': st.secrets["sheets"]["tasks_sheet_id"],
            'credentials': st.secrets["sheets"]["credentials_sheet_id"],
            'projects': st.secrets["sheets"]["projects_sheet_id"]
        }
    except KeyError as e:
        st.error(f"Missing sheet configuration in secrets: {e}")
        return {
            'tasks': "1H4l40IhqeqLhAvM9JwTfIf5u_EHU_-ep",
            'credentials': "1MhzThPgYHkMbcTLcNqMyB6teuWm022_tV3plMPBQ-20",
            'projects': "1gOMPaQRPk8jHIqgZ7kSbv6UW3ZYd1S5f"
        }

# === Initialize Google Sheets Connection ===
@st.cache_resource
def init_google_sheets():
    """Initialize connection to Google Sheets using service account credentials."""
    try:
        # Get credentials from Streamlit secrets
        credentials_dict = st.secrets["google_service_account"]
        
        # Create a clean dictionary for credentials
        clean_credentials = {}
        for key, value in credentials_dict.items():
            if key == "private_key":
                # Clean up the private key - remove extra whitespace and ensure proper formatting
                private_key = str(value).strip()
                if not private_key.startswith("-----BEGIN PRIVATE KEY-----"):
                    private_key = "-----BEGIN PRIVATE KEY-----\n" + private_key
                if not private_key.endswith("-----END PRIVATE KEY-----"):
                    private_key = private_key + "\n-----END PRIVATE KEY-----"
                clean_credentials[key] = private_key
            else:
                clean_credentials[key] = str(value).strip()
        
        # Create credentials object
        credentials = Credentials.from_service_account_info(
            clean_credentials, scopes=SCOPES
        )
        
        # Authorize and return client
        client = gspread.authorize(credentials)
        return client
        
    except KeyError as e:
        st.error(f"Missing credential key in secrets: {e}")
        st.error("Please check your Streamlit secrets configuration.")
        return None
    except ValueError as e:
        if "Incorrect padding" in str(e):
            st.error("❌ Private key formatting error. Please check your private key in secrets.")
            st.error("💡 Tip: Make sure your private key includes the BEGIN/END lines and has no extra spaces.")
            with st.expander("🔧 How to fix private key issues"):
                st.markdown("""
                **Common fixes for private key errors:**
                
                1. **Check the format**: Your private key should look like:
                ```
                -----BEGIN PRIVATE KEY-----
                MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSk...
                ... (multiple lines) ...
                -----END PRIVATE KEY-----
                ```
                
                2. **Remove extra spaces**: Make sure there are no trailing spaces
                
                3. **Use triple quotes**: In TOML, wrap the key with triple quotes:
                ```toml
                private_key = \"\"\"
                -----BEGIN PRIVATE KEY-----
                ...
                -----END PRIVATE KEY-----
                \"\"\"
                ```
                
                4. **Download fresh credentials**: Get a new service account key file from Google Cloud Console
                """)
        else:
            st.error(f"Authentication error: {e}")
        return None
    except Exception as e:
        st.error(f"Failed to connect to Google Sheets: {e}")
        st.error("Please verify your Google Cloud setup and service account permissions.")
        return None

# === Load Tasks from Google Sheets ===
def load_tasks_from_sheets():
    """Load tasks from Google Sheets with caching and rate limiting."""
    # Check cache first
    cached_df = get_cached_data('tasks')
    if cached_df is not None:
        return cached_df
    
    try:
        client = init_google_sheets()
        if client is None:
            return pd.DataFrame()
        
        # Apply rate limiting
        rate_limit_api_call()
        
        sheet_ids = get_sheet_ids()
        sheet = client.open_by_key(sheet_ids['tasks']).sheet1
        data = sheet.get_all_records()
        
        if not data:
            df = pd.DataFrame(columns=[
                "task_name", "project_name", "assigned_to", "priority", "status",
                "start_date", "due_date", "completion_date", "comments", "created_by"
            ])
        else:
            df = pd.DataFrame(data)
            
            # Convert date columns
            date_columns = ['start_date', 'due_date', 'completion_date']
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Cache the result
        set_cached_data('tasks', df)
        return df
        
    except Exception as e:
        st.error(f"Error loading tasks: {e}")
        return pd.DataFrame()

# === Save Tasks to Google Sheets ===
def save_tasks_to_sheets(df):
    """Save tasks DataFrame to Google Sheets - OVERWRITES all data."""
    try:
        client = init_google_sheets()
        if client is None:
            return False
        
        sheet_ids = get_sheet_ids()
        sheet = client.open_by_key(sheet_ids['tasks']).sheet1
        
        # Convert DataFrame to list of lists for Google Sheets
        # First, convert dates to strings
        df_copy = df.copy()
        date_columns = ['start_date', 'due_date', 'completion_date']
        for col in date_columns:
            if col in df_copy.columns:
                df_copy[col] = df_copy[col].dt.strftime('%Y-%m-%d') if df_copy[col].dtype == 'datetime64[ns]' else df_copy[col]
        
        # Clear existing data and add new data (this is for bulk updates)
        sheet.clear()
        
        # Add headers
        headers = df_copy.columns.tolist()
        sheet.append_row(headers)
        
        # Add data rows
        for _, row in df_copy.iterrows():
            sheet.append_row(row.tolist())
        
        return True
    except Exception as e:
        st.error(f"Error saving tasks: {e}")
        return False


def save_tasks_bulk_to_sheets(task_dicts, max_retries=5):
    """Append multiple tasks to the sheet in a single API call with retry/backoff.
    task_dicts: list of task dicts with the same keys used by save_task_to_sheets
    """
    try:
        if not task_dicts:
            return True

        client = init_google_sheets()
        if client is None:
            return False

        # Apply rate limiting
        rate_limit_api_call()

        sheet_ids = get_sheet_ids()
        sheet = client.open_by_key(sheet_ids['tasks']).sheet1

        # Ensure headers exist
        try:
            headers_row = sheet.row_values(1)
            has_headers = len(headers_row) > 0
        except Exception:
            headers_row = []
            has_headers = False

        expected_headers = [
            "task_name", "description", "project_name", "assigned_to",
            "priority", "status", "start_date", "due_date", 
            "completion_date", "comments", "created_by"
        ]

        if not has_headers or len(headers_row) < len(expected_headers):
            sheet.clear()
            sheet.append_row(expected_headers)
            headers_row = expected_headers

        # Create flexible mapping
        header_variations = {
            "task_name": ["task_name", "Task Name", "Task", "task", "name"],
            "description": ["description", "Description", "desc", "Desc"],
            "project_name": ["project_name", "Project Name", "Project", "project"],
            "assigned_to": ["assigned_to", "Assigned To", "Assignee", "assignee", "assigned"],
            "priority": ["priority", "Priority", "pri"],
            "status": ["status", "Status", "stat"],
            "start_date": ["start_date", "Start Date", "start", "Start"],
            "due_date": ["due_date", "Due Date", "due", "Due"],
            "completion_date": ["completion_date", "Completion Date", "completed", "Completed"],
            "comments": ["comments", "Comments", "comment", "Comment", "notes", "Notes"],
            "created_by": ["created_by", "Created By", "creator", "Creator"]
        }

        # Build mapping from headers_row
        column_mapping = {}
        for i, header in enumerate(headers_row):
            header_lower = header.lower().strip()
            for expected_field, variations in header_variations.items():
                if header in variations or header_lower in [v.lower() for v in variations]:
                    column_mapping[expected_field] = i
                    break

        # Build rows aligned to headers_row
        rows = []
        for task in task_dicts:
            task_row = [""] * len(headers_row)
            for field in [
                "task_name", "description", "project_name", "assigned_to",
                "priority", "status", "start_date", "due_date",
                "completion_date", "comments", "created_by"
            ]:
                value = task.get(field, "")
                if field in column_mapping:
                    idx = column_mapping[field]
                    if hasattr(value, 'strftime'):
                        task_row[idx] = value.strftime('%Y-%m-%d')
                    elif value is None or str(value).lower() == 'nat':
                        task_row[idx] = ""
                    else:
                        task_row[idx] = value
            rows.append(task_row)

        # Try to append rows in a single API call with exponential backoff retries
        attempt = 0
        while attempt < max_retries:
            try:
                sheet.append_rows(rows, value_input_option='USER_ENTERED')
                invalidate_cache('tasks')
                return True
            except APIError as e:
                errstr = str(e)
                # If quota error or 429, backoff and retry
                if 'Quota exceeded' in errstr or '429' in errstr:
                    attempt += 1
                    sleep_time = (2 ** attempt) + random.random()
                    time.sleep(sleep_time)
                    continue
                else:
                    st.error(f"Error saving tasks: {e}")
                    return False

        st.error("Failed to save tasks after multiple retries due to quota limits. Please try again in a moment.")
        return False
    except Exception as e:
        st.error(f"Error saving tasks (bulk): {e}")
        return False

# === Load Users from Google Sheets ===
def load_users_from_sheets():
    """Load users from Google Sheets with caching and rate limiting."""
    # Check cache first
    cached_users = get_cached_data('users')
    if cached_users is not None:
        return cached_users
    
    try:
        client = init_google_sheets()
        if client is None:
            return []
        
        # Apply rate limiting
        rate_limit_api_call()
        
        sheet_ids = get_sheet_ids()
        sheet = client.open_by_key(sheet_ids['credentials']).sheet1
        data = sheet.get_all_records()
        
        if not data:
            users_list = []
        else:
            df = pd.DataFrame(data)
            # Clean column names and data (handle trailing spaces)
            df.columns = df.columns.str.strip()
            df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
            
            users_list = df["email"].dropna().unique().tolist()
        
        # Cache the result
        set_cached_data('users', users_list)
        return users_list
        
    except Exception as e:
        st.error(f"Error loading users: {e}")
        return []

# === Get User Name from Google Sheets ===
def get_user_name_from_sheets(user_email):
    """Get user name from Google Sheets credentials with caching and rate limiting."""
    # Check cache first
    cache_key = f'user_name_{user_email}'
    cached_name = get_cached_data(cache_key)
    if cached_name is not None:
        return cached_name
    
    try:
        client = init_google_sheets()
        if client is None:
            return user_email
        
        # Apply rate limiting
        rate_limit_api_call()
        
        sheet_ids = get_sheet_ids()
        sheet = client.open_by_key(sheet_ids['credentials']).sheet1
        data = sheet.get_all_records()
        
        if not data:
            name = user_email
        else:
            df = pd.DataFrame(data)
            # Clean column names and data (handle trailing spaces)
            df.columns = df.columns.str.strip()
            df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
            
            user_match = df[df["email"].str.lower() == user_email.strip().lower()]
            
            if not user_match.empty:
                # Try to get name from various possible columns - updated to match your CSV structure
                for col in ['Name', 'name', 'username', 'full_name']:
                    if col in df.columns and pd.notna(user_match[col].iloc[0]):
                        name = user_match[col].iloc[0]
                        break
                else:
                    name = user_email
            else:
                name = user_email
        
        # Cache the result
        set_cached_data(cache_key, name)
        return name
    except Exception as e:
        st.error(f"Error getting user name: {e}")
        return user_email

# === Load Projects from Google Sheets ===
def load_projects_from_sheets():
    """Load projects from Google Sheets with caching and rate limiting."""
    # Check cache first
    cached_projects = get_cached_data('projects_list')
    if cached_projects is not None:
        return cached_projects
    
    try:
        client = init_google_sheets()
        if client is None:
            return []
        
        # Apply rate limiting
        rate_limit_api_call()
        
        sheet_ids = get_sheet_ids()
        sheet = client.open_by_key(sheet_ids['projects']).sheet1
        data = sheet.get_all_records()
        
        if not data:
            st.warning("⚠️ Projects sheet is empty. Please add some projects first.")
            projects_list = []
        else:
            df = pd.DataFrame(data)
            
            # Check if project_name column exists
            if 'project_name' not in df.columns:
                st.error("❌ Projects sheet is missing 'project_name' column. Please check sheet structure.")
                projects_list = []
            else:
                projects_list = df["project_name"].dropna().tolist()
        
        # Cache the result
        set_cached_data('projects_list', projects_list)
        return projects_list
        
    except Exception as e:
        st.error(f"Error loading projects: {e}")
        st.error("💡 Tip: Run the sheets diagnostic tool to check your sheet structure.")
        return []

# === Load Full Projects DataFrame from Google Sheets ===
def load_projects_df_from_sheets():
    """Load complete projects DataFrame from Google Sheets with caching and rate limiting."""
    # Check cache first
    cached_df = get_cached_data('projects_df')
    if cached_df is not None:
        return cached_df
    
    try:
        client = init_google_sheets()
        if client is None:
            df = pd.DataFrame(columns=[
                "project_name", "description", "start_date", "end_date", 
                "status", "priority", "created_by"
            ])
            return df
        
        # Apply rate limiting
        rate_limit_api_call()
        
        sheet_ids = get_sheet_ids()
        sheet = client.open_by_key(sheet_ids['projects']).sheet1
        data = sheet.get_all_records()
        
        if not data:
            st.warning("⚠️ Projects sheet is empty. Please add some projects first.")
            df = pd.DataFrame(columns=[
                "project_name", "description", "start_date", "end_date", 
                "status", "priority", "created_by"
            ])
        else:
            df = pd.DataFrame(data)
            
            # Ensure all required columns exist
            required_columns = ["project_name", "description", "start_date", "end_date", "status", "priority", "created_by"]
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                st.error(f"❌ Projects sheet is missing columns: {missing_columns}")
                st.error("💡 Please run the sheets diagnostic tool to fix the sheet structure.")
                df = pd.DataFrame(columns=required_columns)
            else:
                # Convert date columns
                date_columns = ['start_date', 'end_date']
                for col in date_columns:
                    if col in df.columns:
                        df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Cache the result
        set_cached_data('projects_df', df)
        return df
        
    except Exception as e:
        st.error(f"Error loading projects: {e}")
        st.error("💡 Tip: Run the sheets diagnostic tool to check your sheet structure.")
        return pd.DataFrame(columns=[
            "project_name", "description", "start_date", "end_date", 
            "status", "priority", "created_by"
        ])

# === Save Projects to Google Sheets ===
def save_projects_to_sheets(df):
    """Save projects DataFrame to Google Sheets - OVERWRITES all data."""
    try:
        client = init_google_sheets()
        if client is None:
            return False
        
        sheet_ids = get_sheet_ids()
        sheet = client.open_by_key(sheet_ids['projects']).sheet1
        
        # Convert DataFrame to list of lists for Google Sheets
        df_copy = df.copy()
        date_columns = ['start_date', 'end_date']
        for col in date_columns:
            if col in df_copy.columns:
                df_copy[col] = df_copy[col].dt.strftime('%Y-%m-%d') if df_copy[col].dtype == 'datetime64[ns]' else df_copy[col]
        
        # Clear existing data and add new data (this is for bulk updates)
        sheet.clear()
        
        # Add headers
        headers = df_copy.columns.tolist()
        sheet.append_row(headers)
        
        # Add data rows
        for _, row in df_copy.iterrows():
            sheet.append_row(row.tolist())
        
        return True
    except Exception as e:
        st.error(f"Error saving projects: {e}")
        return False

# === Save Single Project to Google Sheets ===
def save_project_to_sheets(project_dict):
    """Save a single project to Google Sheets - APPENDS to existing data."""
    try:
        client = init_google_sheets()
        if client is None:
            return False
        
        sheet_ids = get_sheet_ids()
        sheet = client.open_by_key(sheet_ids['projects']).sheet1
        
        # Get existing data to check if headers exist
        try:
            existing_data = sheet.get_all_records()
            has_headers = len(existing_data) >= 0  # get_all_records returns [] if only headers
        except:
            has_headers = False
        
        # If no headers, add them first
        if not has_headers:
            headers = [
                "project_name", "description", "start_date", "end_date", 
                "status", "priority", "created_by"
            ]
            sheet.append_row(headers)
        
        # Prepare project data for insertion
        project_row = [
            project_dict.get("project_name", ""),
            project_dict.get("description", ""),
            project_dict.get("start_date", ""),
            project_dict.get("end_date", ""),
            project_dict.get("status", ""),
            project_dict.get("priority", ""),
            project_dict.get("created_by", "")
        ]
        
        # Convert dates to strings if they're datetime objects
        for i, value in enumerate(project_row):
            if hasattr(value, 'strftime'):
                project_row[i] = value.strftime('%Y-%m-%d')
            elif value is None or str(value).lower() == 'nat':
                project_row[i] = ""
        
        # Append the new project
        sheet.append_row(project_row)
        
        # Invalidate projects cache since we've modified the data
        invalidate_cache('projects_list')
        invalidate_cache('projects_df')
        
        return True
    except Exception as e:
        st.error(f"Error saving project: {e}")
        return False

# === Update Project in Google Sheets ===
def update_project_in_sheets(project_name, updated_project_dict):
    """Update a specific project in Google Sheets."""
    try:
        client = init_google_sheets()
        if client is None:
            return False
        
        sheet_ids = get_sheet_ids()
        sheet = client.open_by_key(sheet_ids['projects']).sheet1
        
        # Get existing data to find the project
        existing_data = sheet.get_all_records()
        
        # Find the project row
        project_row = None
        for i, record in enumerate(existing_data):
            if record.get('project_name') == project_name:
                project_row = i + 2  # +2 because sheets are 1-indexed and there's a header row
                break
        
        if not project_row:
            st.error(f"Project '{project_name}' not found for update")
            return False
        
        # Prepare updated project data
        project_row_data = [
            updated_project_dict.get("project_name", ""),
            updated_project_dict.get("description", ""),
            updated_project_dict.get("start_date", ""),
            updated_project_dict.get("end_date", ""),
            updated_project_dict.get("status", ""),
            updated_project_dict.get("priority", ""),
            updated_project_dict.get("created_by", "")
        ]
        
        # Convert dates to strings if they're datetime objects
        for i, value in enumerate(project_row_data):
            if hasattr(value, 'strftime'):
                project_row_data[i] = value.strftime('%Y-%m-%d')
            elif value is None or str(value).lower() == 'nat':
                project_row_data[i] = ""
        
        # Update the row
        for col, value in enumerate(project_row_data, start=1):
            sheet.update_cell(project_row, col, value)
        
        # Invalidate projects cache since we've modified the data
        invalidate_cache('projects_list')
        invalidate_cache('projects_df')
        
        return True
    except Exception as e:
        st.error(f"Error updating project: {e}")
        return False

# === Check User Credentials ===
def check_user_credentials(email):
    """Check if user email exists in credentials sheet."""
    try:
        client = init_google_sheets()
        if client is None:
            return False
        
        sheet_ids = get_sheet_ids()
        sheet = client.open_by_key(sheet_ids['credentials']).sheet1
        data = sheet.get_all_records()
        
        if not data:
            return False
        
        df = pd.DataFrame(data)
        # Clean column names and data
        df.columns = df.columns.str.strip()
        df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
        
        match = df[df["email"].str.lower() == email.strip().lower()]
        return not match.empty
    except Exception as e:
        st.error(f"Error checking credentials: {e}")
        return False

# === Save Single Task to Google Sheets ===
def save_task_to_sheets(task_dict):
    """Save a single task to Google Sheets - APPENDS to existing data."""
    try:
        # Validate required fields
        required_fields = ['task_name', 'project_name', 'assigned_to']
        for field in required_fields:
            if not task_dict.get(field):
                st.error(f"Missing required field: {field}")
                return False
        
        client = init_google_sheets()
        if client is None:
            return False
        
        # Apply rate limiting
        rate_limit_api_call()
        
        sheet_ids = get_sheet_ids()
        sheet = client.open_by_key(sheet_ids['tasks']).sheet1
        
        # Get existing data to check if headers exist and if task already exists
        try:
            # Get the first row to check headers
            headers_row = sheet.row_values(1)
            existing_data = sheet.get_all_records()
            has_headers = len(headers_row) > 0
            
            # (silent) current headers are read for internal mapping
            
            # Check if task already exists (for updates)
            existing_task_row = None
            for i, record in enumerate(existing_data):
                # Try different possible field names for task identification
                task_name_field = None
                for possible_field in ['task_name', 'Task Name', 'Task', 'task', 'name']:
                    if possible_field in record:
                        task_name_field = possible_field
                        break
                
                if task_name_field and record.get(task_name_field) == task_dict.get('task_name'):
                    existing_task_row = i + 2  # +2 because sheets are 1-indexed and there's a header row
                    break
        except Exception as e:
            st.error(f"Error reading sheet structure: {e}")
            has_headers = False
            existing_task_row = None
            headers_row = []
        
        # Define the expected headers and create mapping
        expected_headers = [
            "task_name", "description", "project_name", "assigned_to",
            "priority", "status", "start_date", "due_date", 
            "completion_date", "comments", "created_by"
        ]
        
        # Create a flexible mapping for different header variations
        header_variations = {
            "task_name": ["task_name", "Task Name", "Task", "task", "name"],
            "description": ["description", "Description", "desc", "Desc"],
            "project_name": ["project_name", "Project Name", "Project", "project"],
            "assigned_to": ["assigned_to", "Assigned To", "Assignee", "assignee", "assigned"],
            "priority": ["priority", "Priority", "pri"],
            "status": ["status", "Status", "stat"],
            "start_date": ["start_date", "Start Date", "start", "Start"],
            "due_date": ["due_date", "Due Date", "due", "Due"],
            "completion_date": ["completion_date", "Completion Date", "completed", "Completed"],
            "comments": ["comments", "Comments", "comment", "Comment", "notes", "Notes"],
            "created_by": ["created_by", "Created By", "creator", "Creator"]
        }
        
        # If no headers or headers are incomplete, set up the sheet properly (silent)
        if not has_headers or len(headers_row) < len(expected_headers):
            # Clear the sheet and add proper headers
            sheet.clear()
            sheet.append_row(expected_headers)
            headers_row = expected_headers
            has_headers = True
        
    # Create column mapping based on actual headers with flexibility
        column_mapping = {}
        for i, header in enumerate(headers_row):
            header_lower = header.lower().strip()
            for expected_field, variations in header_variations.items():
                if header in variations or header_lower in [v.lower() for v in variations]:
                    column_mapping[expected_field] = i
                    break
        
        # Prepare task data for insertion - map to correct columns
        task_row = [""] * len(headers_row)  # Initialize with empty strings
        
        # Map our data to the correct columns
        field_mappings = {
            "task_name": task_dict.get("task_name", ""),
            "description": task_dict.get("description", ""),
            "project_name": task_dict.get("project_name", ""),
            "assigned_to": task_dict.get("assigned_to", ""),
            "priority": task_dict.get("priority", ""),
            "status": task_dict.get("status", ""),
            "start_date": task_dict.get("start_date", ""),
            "due_date": task_dict.get("due_date", ""),
            "completion_date": task_dict.get("completion_date", ""),
            "comments": task_dict.get("comments", ""),
            "created_by": task_dict.get("created_by", "")
        }
        
        # Fill the task_row array with data in correct positions
        for field, value in field_mappings.items():
            if field in column_mapping:
                col_index = column_mapping[field]
                task_row[col_index] = value
        
        # Column mapping created (no UI debug output)
        missing_fields = [field for field in field_mappings.keys() if field not in column_mapping]
        
        # Convert dates to strings if they're datetime objects
        for i, value in enumerate(task_row):
            if hasattr(value, 'strftime'):
                task_row[i] = value.strftime('%Y-%m-%d')
            elif value is None or str(value).lower() == 'nat':
                task_row[i] = ""
        
        # Data prepared for save (no UI debug output)
        
        # If task exists, update it; otherwise append new task
        if existing_task_row:
            # Update existing task (silent)
            for col, value in enumerate(task_row, start=1):
                sheet.update_cell(existing_task_row, col, value)
        else:
            # Append new task (silent)
            sheet.append_row(task_row)
        
        # Invalidate tasks cache since we've modified the data
        invalidate_cache('tasks')
        
        return True
    except Exception as e:
        st.error(f"Error saving task: {e}")
        # Log more details for debugging
        import traceback
        st.error(f"Task save error details: {traceback.format_exc()}")
        return False

# === Update Task in Google Sheets ===
def update_task_in_sheets(task_name, updated_task_dict):
    """Update a specific task in Google Sheets using flexible column mapping."""
    try:
        client = init_google_sheets()
        if client is None:
            return False
        
        # Apply rate limiting
        rate_limit_api_call()
        
        sheet_ids = get_sheet_ids()
        sheet = client.open_by_key(sheet_ids['tasks']).sheet1
        
        # Get headers and existing data
        headers_row = sheet.row_values(1)
        existing_data = sheet.get_all_records()
        
        # (silent) current headers read for mapping
        
        # Create flexible column mapping like in save_task_to_sheets
        header_variations = {
            "task_name": ["task_name", "Task Name", "Task", "task", "name"],
            "description": ["description", "Description", "desc", "Desc"],
            "project_name": ["project_name", "Project Name", "Project", "project"],
            "assigned_to": ["assigned_to", "Assigned To", "Assignee", "assignee", "assigned"],
            "priority": ["priority", "Priority", "pri"],
            "status": ["status", "Status", "stat"],
            "start_date": ["start_date", "Start Date", "start", "Start"],
            "due_date": ["due_date", "Due Date", "due", "Due"],
            "completion_date": ["completion_date", "Completion Date", "completed", "Completed"],
            "comments": ["comments", "Comments", "comment", "Comment", "notes", "Notes"],
            "created_by": ["created_by", "Created By", "creator", "Creator"]
        }
        
        # Create column mapping based on actual headers
        column_mapping = {}
        for i, header in enumerate(headers_row):
            header_lower = header.lower().strip()
            for expected_field, variations in header_variations.items():
                if header in variations or header_lower in [v.lower() for v in variations]:
                    column_mapping[expected_field] = i
                    break
        
        # Column mapping created (no UI debug output)
        
        # Find the task row
        task_row = None
        for i, record in enumerate(existing_data):
            # Try different possible field names for task identification
            task_name_field = None
            for possible_field in ['task_name', 'Task Name', 'Task', 'task', 'name']:
                if possible_field in record:
                    task_name_field = possible_field
                    break
            
            if task_name_field and record.get(task_name_field) == task_name:
                task_row = i + 2  # +2 because sheets are 1-indexed and there's a header row
                break
        
        if not task_row:
            st.error(f"Task '{task_name}' not found for update")
            return False
        
        # Map our data to the correct columns
        field_mappings = {
            "task_name": updated_task_dict.get("task_name", ""),
            "description": updated_task_dict.get("description", ""),
            "project_name": updated_task_dict.get("project_name", ""),
            "assigned_to": updated_task_dict.get("assigned_to", ""),
            "priority": updated_task_dict.get("priority", ""),
            "status": updated_task_dict.get("status", ""),
            "start_date": updated_task_dict.get("start_date", ""),
            "due_date": updated_task_dict.get("due_date", ""),
            "completion_date": updated_task_dict.get("completion_date", ""),
            "comments": updated_task_dict.get("comments", ""),
            "created_by": updated_task_dict.get("created_by", "")
        }
        
        # Convert dates to strings if they're datetime objects
        for field, value in field_mappings.items():
            if hasattr(value, 'strftime'):
                field_mappings[field] = value.strftime('%Y-%m-%d')
            elif value is None or str(value).lower() == 'nat':
                field_mappings[field] = ""
        
        # Update only the mapped columns
        updated_count = 0
        for field, value in field_mappings.items():
            if field in column_mapping:
                col_index = column_mapping[field] + 1  # +1 for 1-indexed columns
                sheet.update_cell(task_row, col_index, value)
                updated_count += 1
        
        # Update completed (no UI debug output)
        missing_fields = [field for field in field_mappings.keys() if field not in column_mapping]
        
        # Invalidate tasks cache since we've modified the data
        invalidate_cache('tasks')
        
        return True
    except Exception as e:
        st.error(f"Error updating task: {e}")
        return False

# Work Allocation Tool

A cloud-based work allocation and project management tool built with Streamlit and Google Sheets integration.

## 🌟 Features

- **User Authentication**: Secure login system with domain validation
- **Project Management**: Create, view, and manage projects
- **Task Management**: Assign, track, and update task statuses
- **Dashboard Analytics**: Visual insights with charts and metrics
- **Google Sheets Integration**: All data stored in Google Sheets (no local files)
- **Real-time Collaboration**: Multiple users can work simultaneously

## 🏗️ Architecture

The application is completely cloud-based and uses:
- **Frontend**: Streamlit web application
- **Backend**: Google Sheets as database
- **Authentication**: Google Service Account
- **Data Storage**: Google Drive/Sheets

### Data Structure

The application uses three Google Sheets:
1. **Credentials Sheet**: User authentication and profile data
2. **Projects Sheet**: Project information and status
3. **Tasks Sheet**: Task assignments and tracking

## 🚀 Deployment

### Prerequisites

1. Google Cloud Project with Sheets API enabled
2. Google Service Account with proper permissions
3. Three Google Sheets created for data storage
4. Streamlit Cloud account (or other hosting platform)

### Setup Instructions

#### 1. Google Cloud Setup

1. Create a Google Cloud Project
2. Enable Google Sheets API and Google Drive API
3. Create a Service Account
4. Download the service account JSON key
5. Share your Google Sheets with the service account email

#### 2. Google Sheets Setup

Create three Google Sheets with the following structures:

**Credentials Sheet**:
- Column A: email
- Column B: Name (or name, username, full_name)

**Projects Sheet**:
- Column A: project_name
- Column B: description
- Column C: start_date
- Column D: end_date
- Column E: status
- Column F: priority
- Column G: created_by

**Tasks Sheet**:
- Column A: task_name
- Column B: description
- Column C: project_name
- Column D: assigned_to
- Column E: priority
- Column F: status
- Column G: start_date
- Column H: due_date
- Column I: completion_date
- Column J: comments
- Column K: created_by

#### 3. Streamlit Secrets Configuration

Add the following to your Streamlit secrets (either `.streamlit/secrets.toml` locally or in Streamlit Cloud secrets):

```toml
[google_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY\n-----END PRIVATE KEY-----"
client_email = "your-service-account@your-project.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com"
universe_domain = "googleapis.com"

[sheets]
tasks_sheet_id = "your-tasks-sheet-id"
credentials_sheet_id = "your-credentials-sheet-id"
projects_sheet_id = "your-projects-sheet-id"
```

#### 4. Deployment

1. Push code to GitHub repository
2. Connect repository to Streamlit Cloud
3. Add secrets in Streamlit Cloud dashboard
4. Deploy application

## 📁 Project Structure

```
Work_Allocation_Tool/
├── app.py                      # Main application entry point
├── Dashboard.py                # Dashboard and analytics
├── Projects.py                 # Project management logic
├── Tasks.py                    # Task management logic
├── google_sheets_integration.py # Google Sheets API integration
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── .gitignore                  # Git ignore rules
├── logos/                      # Company logos for branding
│   ├── childlogo.jpg          # Child Help Foundation logo
│   └── tigerlogo.jpg          # Tiger Analytics logo
└── .streamlit/
    └── secrets.toml            # Local secrets (not committed)
```

## 🔧 Configuration

### Environment Variables

The application uses Streamlit secrets for configuration. No local files are required.

### Email Domain Validation

Currently supports these domains:
- childhelpfoundationindia.org
- tigeranalytics.com
- skypathdigital.com

To modify, update the `validate_email()` function in `app.py`.

### Admin Users

Admin privileges (project/task creation) are granted to:
- digital@childhelpfoundationindia.org

To modify, update the admin checks in the respective modules.

## 🎯 Usage

### User Login
1. Enter your email address
2. System validates against authorized domains
3. System checks if user exists in credentials sheet

### Dashboard
- View project and task statistics
- Interactive charts and filters
- Real-time data from Google Sheets

### Project Management
- Create new projects (admin only)
- View project details
- Edit project status
- Track project completion

### Task Management
- Create new tasks (admin only)
- Assign tasks to users
- Update task status
- View personal tasks
- Track task completion

## 🔒 Security

- Domain-based email validation
- Google Service Account authentication
- No sensitive data stored locally
- All data encrypted in Google Sheets

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

This project is proprietary and confidential.

## 🆘 Support

For technical support or questions, contact the development team.

## 🔄 Updates and Maintenance

The application automatically syncs with Google Sheets. No manual data migration required for updates.

## 📊 Data Backup

Data is automatically backed up through Google Sheets version history and Google Drive backup systems.
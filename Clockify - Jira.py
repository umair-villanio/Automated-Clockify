import requests
import yaml
from datetime import datetime, timedelta
from base64 import b64encode
from dotenv import dotenv_values

# Load environment variables from the .env file
config = dotenv_values(".env")

# Clockify API credentials
API_KEY = ""
WORKSPACE_ID = ""
BASE_URL = "https://api.clockify.me/api/v1"
WORKSPACES_URL = f"{BASE_URL}/workspaces"
TIME_ENTRIES_URL = "https://api.clockify.me/api/v1/workspaces/{WORKSPACE_ID}/time-entries"

# Jira API credentials
JIRA_USERNAME = config["JIRA_USERNAME"]
JIRA_API_TOKEN = config["JIRA_API_TOKEN"]
JIRA_URL = config["JIRA_URL"]
JIRA_ISSUES_URL = f"{JIRA_URL}/rest/api/2/search"

# Global variables
jira_issues = []
projects_data = {}


def load_projects(file_path):
    """
    Load projects and leave projects from a YAML file.
    """
    with open(file_path, "r") as f:
        return yaml.safe_load(f)


def get_jira_issues():
    """
    Fetch Jira issues assigned to the user.
    """
    global jira_issues
    auth_string = f"{JIRA_USERNAME}:{JIRA_API_TOKEN}"
    b64_auth_string = b64encode(auth_string.encode()).decode()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {b64_auth_string}"
    }

    query_params = {
        "jql": "assignee=currentUser() AND status!=Done",
        "fields": "summary"
    }

    print()
    print()

    response = requests.get(JIRA_ISSUES_URL, headers=headers, params=query_params)

    if response.status_code == 200:
        issues = response.json().get('issues', [])
        if issues:
            print("Jira Issues Assigned:")
            for i, issue in enumerate(issues, start=1):
                issue_key = issue['key']
                issue_summary = issue['fields']['summary']
                print(f"{i}. [{issue_key}]: {issue_summary}")
                jira_issues.append(f"[{issue_key}]: {issue_summary}")
        else:
            print("No unresolved Jira issues assigned.")
    else:
        print(f"Error fetching Jira issues: {response.status_code}")
        print(response.text)


def format_time(month, day, hour, minute):
    """
    Convert time to UTC and format it for Clockify.
    """
    current_time = datetime.utcnow()
    year = current_time.year
    input_time = datetime(year, month, day, hour, minute)
    adjusted_time = input_time - timedelta(hours=5, minutes=30)
    formatted_time = adjusted_time.isoformat() + 'Z'
    return formatted_time


def create_time_entry(api_key, workspace_id, project_id, description, start, end):
    """
    Create a new time entry in Clockify.
    """
    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": API_KEY,
    }

    data = {
        "start": start,
        "end": end,
        "description": description,
        "projectId": project_id,
        "billable": False,
    }

    response = requests.post(TIME_ENTRIES_URL, headers=headers, json=data)

    if response.status_code == 201:
        print("Time entry created successfully")
    else:
        print(f"Error creating time entry. Status code: {response.status_code}")
        print(response.text)


def create_project_time_entries(project_number, month, start_day, end_day, description):
    """
    Create time entries for the selected project between the given start and end days.
    """
    project_id = projects_data['projects'][project_number]['id']
    leave_projects = projects_data['leave_projects']

    for x in range(start_day, end_day + 1):
        weekday = datetime(datetime.utcnow().year, month, x).weekday()

        if weekday == 5 or weekday == 6:  # Skip weekends
            print(f"Skipping entry for day {x} (Saturday/Sunday)")
            continue

        if project_id in leave_projects:
            # Handle leave entry
            create_time_entry(API_KEY, WORKSPACE_ID, project_id, description, 
                              format_time(month, x, 9, 0), format_time(month, x, 17, 0))
            print(f"Leave entry created for day {x} (9:00 - 17:00)")
            continue

        if weekday == 1:  # Tuesday
            # Create time entries for Tuesday
            create_time_entry(API_KEY, WORKSPACE_ID, project_id, description, 
                              format_time(month, x, 9, 0), format_time(month, x, 10, 30))
            create_time_entry(API_KEY, WORKSPACE_ID, project_id, description, 
                              format_time(month, x, 11, 0), format_time(month, x, 13, 0))
            create_time_entry(API_KEY, WORKSPACE_ID, project_id, description, 
                              format_time(month, x, 13, 30), format_time(month, x, 17, 0))

            continue

        if weekday == 4:  # Friday
            # Create time entries for Friday
            create_time_entry(API_KEY, WORKSPACE_ID, project_id, description, format_time(month, x, 9, 0), format_time(month, x, 11, 30))
            create_time_entry(API_KEY, WORKSPACE_ID, project_id, description, format_time(month, x, 13, 0), format_time(month, x, 18, 0))
            # SMT-87 meeting entry
            
        else:
            # Handle regular weekdays
            create_time_entry(API_KEY, WORKSPACE_ID, project_id, description, format_time(month, x, 9, 0), format_time(month, x, 13, 0))
            create_time_entry(API_KEY, WORKSPACE_ID, project_id, description, format_time(month, x, 13, 30), format_time(month, x, 17, 0))
            


def main():
    """
    Main function to execute the program.
    """
    global projects_data

    # Load projects and leave projects from the YAML file
    projects_data = load_projects("projects.yaml")

    # Display project list
    print("Projects:")
    for i, project in enumerate(projects_data['projects'], start=1):
        print(f"{i}. {project['name']}")

    # Fetch Jira issues assigned to the user
    get_jira_issues()
    print()
    print()

    # User input for Clockify time entries
    project_number = int(input("Enter project number: ")) - 1
    month = int(input("Enter the month (1-12): "))
    start_day = int(input("Enter the start day: "))
    end_day = int(input("Enter the end day: "))

    # Allow the user to select a Jira issue for the description
    if jira_issues:
        descinput = int(input("Select Jira issue for description (enter the number): ")) - 1
        description = jira_issues[descinput]
    else:
        description = input("Enter the description: ")

    # Create time entries for the project
    create_project_time_entries(project_number, month, start_day, end_day, description)


if __name__ == "__main__":
    main()

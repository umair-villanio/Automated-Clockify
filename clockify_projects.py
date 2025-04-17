import requests
from dotenv import dotenv_values

# Load environment variables from the .env file
config = dotenv_values(".env")

# Get API Key and Base URL directly from the loaded config
API_KEY = config["CLOCKIFY_API_KEY"]
BASE_URL = config["CLOCKIFY_BASE_URL"]

# Headers for authentication
HEADERS = {
    "X-Api-Key": API_KEY
}

def get_projects(workspace_id):
    """Retrieve all projects in a workspace, handling pagination."""
    projects = []
    page = 1
    page_size = 50  # Adjust page size as needed (maximum is 100)
    
    while True:
        url = f"{BASE_URL}/workspaces/{workspace_id}/projects?page={page}&pageSize={page_size}"
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            if not data:  # Break if no more projects
                break
            projects.extend(data)
            page += 1
        else:
            print(f"Error fetching projects for workspace {workspace_id}: {response.text}")
            break
    
    return projects

def get_workspaces():
    """Retrieve all workspaces available in the account."""
    url = f"{BASE_URL}/workspaces"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        print("Error fetching workspaces:", response.text)
        return []

def main():
    # Get user input for the search term
    search_term = input("Enter a word to search in project names: ").strip().lower()

    # Get all workspaces
    workspaces = get_workspaces()
    if not workspaces:
        print("No workspaces found.")
        return

    for workspace in workspaces:
        print(f"Workspace: {workspace['name']} (ID: {workspace['id']})")
        # Fetch projects for each workspace
        projects = get_projects(workspace['id'])
        if projects:
            print("Matching Projects:")
            matching_projects = [
                project for project in projects 
                if search_term in project['name'].lower()
            ]
            if matching_projects:
                for project in matching_projects:
                    print(f" - {project['name']} (ID: {project['id']})")
            else:
                print(f"No projects match the search term '{search_term}'.")
        else:
            print("No projects found in this workspace.")
        print("-" * 50)

if __name__ == "__main__":
    main()
    close = input("Press Enter to close.")

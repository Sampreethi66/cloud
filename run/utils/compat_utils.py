import nbformat

def create_local_compatible_notebook(source_file, output_file):
    """Create a local-compatible version of the notebook"""
    with open(source_file, 'r') as f:
        nb = nbformat.read(f, as_version=4)

    # Create a new notebook with local-compatible code
    new_cells = []

    # Add parameters cell for papermill
    parameters_cell = nbformat.v4.new_code_cell(
        source="""# Parameters (injected by papermill)
LOCAL_EXECUTION = False
GITHUB_TOKEN = ""
TARGET_REPO = ""
TARGET_FOLDER = ""
EXECUTION_ENVIRONMENT = ""
LOCAL_SERVER_URL = ""
LOCAL_HOSTNAME = ""
LOCAL_IP = ""
PLATFORM = ""
PYTHON_VERSION = ""
CURRENT_YEAR = 2025
""",
        metadata={"tags": ["parameters"]}
    )
    new_cells.append(parameters_cell)

    # Add local compatibility imports
    compatibility_cell = nbformat.v4.new_code_cell(
        source="""# Local compatibility setup
import os
import requests
import base64
import json
from datetime import datetime

# Mock Google Cloud dependencies for local execution
if LOCAL_EXECUTION:
    print("🔧 Running in local mode - using environment variables instead of Google Cloud Secret Manager")

    # Use environment GITHUB_TOKEN instead of Secret Manager
    def get_github_token():
        token = GITHUB_TOKEN or os.environ.get('GITHUB_TOKEN')
        if token:
            print("✅ GitHub token found in environment")
            return token
        else:
            print("❌ No GitHub token found - set GITHUB_TOKEN environment variable")
            return None
else:
    # Original cloud code
    try:
        from google.cloud import secretmanager

        def get_github_token():
            try:
                client = secretmanager.SecretManagerServiceClient()
                name = f"projects/{os.environ.get('GOOGLE_CLOUD_PROJECT')}/secrets/github-token/versions/latest"
                response = client.access_secret_version(request={"name": name})
                return response.payload.data.decode("UTF-8")
            except Exception as e:
                print(f"Error getting GitHub token: {e}")
                return None
    except ImportError:
        print("Google Cloud dependencies not available")
        def get_github_token():
            return os.environ.get('GITHUB_TOKEN')

GITHUB_TOKEN = get_github_token()
print(f"GitHub token available: {GITHUB_TOKEN is not None}")

# Set up folder structure based on environment
if LOCAL_EXECUTION:
    # For local execution, use current year + '-local'
    reports_folder = TARGET_FOLDER  # This will be '2025-local'
    execution_report = f'''
## Execution Report

**Environment:** {EXECUTION_ENVIRONMENT}
**Target Folder:** {reports_folder}
**Server:** {LOCAL_SERVER_URL}
**Hostname:** {LOCAL_HOSTNAME}
**Local IP:** {LOCAL_IP}
**Platform:** {PLATFORM}
**Python Version:** {PYTHON_VERSION}
**Execution Time:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**GitHub Token Status:** {"✅ Configured" if GITHUB_TOKEN else "❌ Not found"}

---
'''
    print("📋 Execution Report:")
    print(execution_report)
else:
    # For cloud execution, use current year + '-cloud'
    reports_folder = f"{CURRENT_YEAR}-cloud"
    execution_report = f'''
## Execution Report

**Environment:** Google Cloud Run
**Target Folder:** {reports_folder}
**Execution Time:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**GitHub Token Status:** {"✅ Configured" if GITHUB_TOKEN else "❌ Not found"}

---
'''

# Make reports_folder available for the notebook to use
print(f"📁 Reports will be saved to folder: {reports_folder}")
"""
    )
    new_cells.append(compatibility_cell)

    # Add the rest of the cells, skipping the problematic imports and modifying upload function
    for cell in nb.cells:
        if cell.cell_type == 'code':
            # Skip cells that import google.cloud directly
            if ('from google.cloud import secretmanager' in cell.source or
                'import secretmanager' in cell.source or
                'def get_github_token():' in cell.source or
                'GITHUB_TOKEN = get_github_token()' in cell.source):
                continue

            # Modify the upload function to use TARGET_FOLDER
            if 'def upload_reports_to_github(' in cell.source:
                # Replace the hardcoded "reports" path with dynamic folder
                modified_source = cell.source.replace(
                    'file_path = f"reports/execution-{datetime.now().strftime(\'%Y%m%d-%H%M%S\')}.md"',
                    'file_path = f"{reports_folder}/execution-{datetime.now().strftime(\'%Y%m%d-%H%M%S\')}.md"'
                )
                cell.source = modified_source

        new_cells.append(cell)

    # Create new notebook with proper metadata
    new_nb = nbformat.v4.new_notebook(cells=new_cells)

    # Set kernel metadata
    new_nb.metadata = {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.12.0"
        }
    }

    # Write the modified notebook
    with open(output_file, 'w') as f:
        nbformat.write(new_nb, f)

    print(f"📝 Created local-compatible notebook: {output_file}")


def create_cloud_compatible_notebook(source_file, output_file):
    """Create a cloud-compatible version of the notebook (uses original Google Cloud imports)"""
    with open(source_file, 'r') as f:
        nb = nbformat.read(f, as_version=4)

    # Create a new notebook with cloud-compatible code
    new_cells = []

    # Add parameters cell for papermill
    parameters_cell = nbformat.v4.new_code_cell(
        source="""# Parameters (injected by papermill)
LOCAL_EXECUTION = False
GITHUB_TOKEN = ""
TARGET_REPO = ""
TARGET_FOLDER = ""
EXECUTION_ENVIRONMENT = ""
CURRENT_YEAR = 2025
""",
        metadata={"tags": ["parameters"]}
    )
    new_cells.append(parameters_cell)

    # Add cloud compatibility imports
    compatibility_cell = nbformat.v4.new_code_cell(
        source="""# Cloud compatibility setup
import os
import requests
import base64
import json
from datetime import datetime
from google.cloud import secretmanager

# Get the GitHub token from Secret Manager (cloud execution)
def get_github_token():
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{os.environ.get('GOOGLE_CLOUD_PROJECT')}/secrets/github-token/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        print(f"Error getting GitHub token: {e}")
        return None

GITHUB_TOKEN = get_github_token()
print(f"GitHub token available: {GITHUB_TOKEN is not None}")

# Set up folder structure for cloud execution
reports_folder = TARGET_FOLDER  # This will be '{year}-cloud'
execution_report = f'''
## Execution Report

**Environment:** {EXECUTION_ENVIRONMENT}
**Target Folder:** {reports_folder}
**Execution Time:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**GitHub Token Status:** {"✅ Configured" if GITHUB_TOKEN else "❌ Not found"}

---
'''

# Make reports_folder available for the notebook to use
print(f"📁 Reports will be saved to folder: {reports_folder}")
"""
    )
    new_cells.append(compatibility_cell)

    # Add the rest of the cells, skipping the problematic imports and modifying upload function
    for cell in nb.cells:
        if cell.cell_type == 'code':
            # Skip cells that import google.cloud directly (since we handle it above)
            if ('from google.cloud import secretmanager' in cell.source or
                'def get_github_token():' in cell.source or
                'GITHUB_TOKEN = get_github_token()' in cell.source):
                continue

            # Modify the upload function to use TARGET_FOLDER
            if 'def upload_reports_to_github(' in cell.source:
                # Replace the hardcoded "reports" path with dynamic folder
                modified_source = cell.source.replace(
                    'file_path = f"reports/execution-{datetime.now().strftime(\'%Y%m%d-%H%M%S\')}.md"',
                    'file_path = f"{reports_folder}/execution-{datetime.now().strftime(\'%Y%m%d-%H%M%S\')}.md"'
                )
                cell.source = modified_source

        new_cells.append(cell)

    # Create new notebook with proper metadata
    new_nb = nbformat.v4.new_notebook(cells=new_cells)

    # Set kernel metadata
    new_nb.metadata = {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.12.0"
        }
    }

    # Write the modified notebook
    with open(output_file, 'w') as f:
        nbformat.write(new_nb, f)

    print(f"📝 Created cloud-compatible notebook: {output_file}")


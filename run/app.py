# Import compatibility fixes first
try:
    import fix_imports
except ImportError:
    pass

import os
import sys
import tempfile
import subprocess
import requests
import json
import yaml
from flask import Flask, request, jsonify

# Load environment variables from .env file for local development
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, skip for production

# Check if running on Google Cloud (Secret Manager)
try:
    from google.cloud import secretmanager
    CLOUD_AVAILABLE = True
except ImportError:
    CLOUD_AVAILABLE = False
    print("⚠️  Google Cloud dependencies not available - running in local mode", file=sys.stderr)

# Try to import notebook execution dependencies
try:
    import git
    import papermill as pm
    import nbformat
    from nbconvert import HTMLExporter
    NOTEBOOK_EXECUTION_AVAILABLE = True
    print("✅ Notebook execution dependencies available", file=sys.stderr)
except ImportError as e:
    NOTEBOOK_EXECUTION_AVAILABLE = False
    print(f"⚠️  Notebook execution dependencies not available: {e}", file=sys.stderr)
    print("📝 Local interface will work, but notebook execution will be simulated", file=sys.stderr)

app = Flask(__name__)

# === Load configuration from config.yaml ===
def load_config():
    try:
        with open('config.yaml', 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return {
            'github': {
                'source_repo_url': 'https://github.com/modelearth/cloud.git',
                'target_repo': 'https://github.com/modelearth/reports.git',
                'notebook_path': 'run/notebook.ipynb'
            }
        }

config = load_config()
SOURCE_REPO_URL = config['github']['source_repo_url']
TARGET_REPO = config['github']['target_repo']
NOTEBOOK_PATH = config['github']['notebook_path']

# Get the GitHub token from environment variable or Secret Manager
def get_github_token():
    """Retrieve GitHub token from env or Google Secret Manager (GCP)"""
    import sys

    # Try environment variable (local dev)
    token = os.environ.get('GITHUB_TOKEN')
    if token:
        print("[DEBUG] GitHub token loaded from environment variable", file=sys.stderr)
        return token

    # Fallback to Google Cloud Secret Manager
    if CLOUD_AVAILABLE:
        try:
            client = secretmanager.SecretManagerServiceClient()
            project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
            if not project_id:
                print("[ERROR] GOOGLE_CLOUD_PROJECT not set in environment", file=sys.stderr)
                return None

            name = f"projects/{project_id}/secrets/github-token/versions/latest"
            response = client.access_secret_version(request={"name": name})
            token = response.payload.data.decode("UTF-8")

            print(f"[DEBUG] GitHub token retrieved from Secret Manager. Length: {len(token)}", file=sys.stderr)
            return token

        except Exception as e:
            print(f"[ERROR] Failed to retrieve GitHub token from Secret Manager: {e}", file=sys.stderr)
            return None

    print("[ERROR] GitHub token not found: no environment variable and no GCP access", file=sys.stderr)
    return None

@app.route('/')
def home():
    try:
        with open('page.html', 'r') as f:
            return f.read()
    except Exception as e:
        print(f"[ERROR] Failed to load homepage: {e}", file=sys.stderr)
        return "<h2>Error loading homepage</h2>", 500

@app.route('/config')
def config_page():
    with open('index.html', 'r') as f:
        return f.read()

@app.route('/get-config', methods=['GET'])
def get_config():
    try:
        config = load_config()
        return jsonify({
            'status': 'success',
            'config': config
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/save-config', methods=['POST'])
def save_config():
    try:
        data = request.json
        config = load_config()

        # Update configuration with form data
        if 'projectId' in data:
            if 'project' not in config:
                config['project'] = {}
            config['project']['id'] = data['projectId']
        if 'projectName' in data:
            if 'project' not in config:
                config['project'] = {}
            config['project']['name'] = data['projectName']
        if 'region' in data:
            if 'project' not in config:
                config['project'] = {}
            config['project']['region'] = data['region']
        if 'sourceRepo' in data:
            if 'github' not in config:
                config['github'] = {}
            config['github']['source_repo_url'] = data['sourceRepo']
        if 'targetRepo' in data:
            if 'github' not in config:
                config['github'] = {}
            config['github']['target_repo'] = data['targetRepo']
        if 'notebookPath' in data:
            if 'github' not in config:
                config['github'] = {}
            config['github']['notebook_path'] = data['notebookPath']
        if 'serviceName' in data:
            if 'service' not in config:
                config['service'] = {}
            config['service']['name'] = data['serviceName']

        # Save updated configuration
        with open('config.yaml', 'w') as f:
            yaml.dump(config, f, default_flow_style=False)

        # Update global variables
        global SOURCE_REPO_URL, TARGET_REPO, NOTEBOOK_PATH
        SOURCE_REPO_URL = config['github']['source_repo_url']
        TARGET_REPO = config['github']['target_repo']
        NOTEBOOK_PATH = config['github']['notebook_path']

        return jsonify({
            'status': 'success',
            'message': 'Configuration saved successfully'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

def execute_notebook_with_dependencies():
    """Execute notebook with full dependencies (papermill, git, etc.)"""
    try:
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"🔄 Cloning repository: {SOURCE_REPO_URL}")
            # Clone the source repository
            repo = git.Repo.clone_from(SOURCE_REPO_URL, temp_dir)

            # Path to the notebook in the cloned repo
            notebook_file = os.path.join(temp_dir, NOTEBOOK_PATH)
            print(f"📓 Executing notebook: {notebook_file}")

            # Create a local-compatible version of the notebook
            local_notebook_file = os.path.join(temp_dir, 'local_notebook.ipynb')
            create_local_compatible_notebook(notebook_file, local_notebook_file)

            # Execute the local-compatible notebook
            output_path = os.path.join(temp_dir, 'output.ipynb')

            # Parameters to inject for local execution
            import socket
            import platform
            from datetime import datetime

            # Get local server information
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            port = int(os.environ.get('PORT', 8100))
            current_year = datetime.now().year

            # Determine target folder based on execution environment
            target_folder = f"{current_year}-local"

            parameters = {
                'LOCAL_EXECUTION': True,
                'GITHUB_TOKEN': os.environ.get('GITHUB_TOKEN', ''),
                'TARGET_REPO': TARGET_REPO,
                'TARGET_FOLDER': target_folder,
                'EXECUTION_ENVIRONMENT': 'Local Development Server',
                'LOCAL_SERVER_URL': f'http://localhost:{port}',
                'LOCAL_HOSTNAME': hostname,
                'LOCAL_IP': local_ip,
                'PLATFORM': platform.system(),
                'PYTHON_VERSION': platform.python_version(),
                'CURRENT_YEAR': current_year
            }

            pm.execute_notebook(
                local_notebook_file,
                output_path,
                parameters=parameters
            )

            # Read the executed notebook
            with open(output_path, 'r') as f:
                nb = nbformat.read(f, as_version=4)

            # Convert to HTML for display
            html_exporter = HTMLExporter()
            html_data, resources = html_exporter.from_notebook_node(nb)

            print("✅ Notebook executed successfully")
            return {
                'status': 'success',
                'message': 'Notebook executed successfully'
            }
    except Exception as e:
        print(f"❌ Notebook execution failed: {e}")
        return {
            'status': 'error',
            'message': f'Notebook execution failed: {str(e)}'
        }

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

def execute_notebook_cloud():
    """Execute notebook in Google Cloud environment with year-based folders"""
    try:
        from datetime import datetime

        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"🔄 Cloning repository: {SOURCE_REPO_URL}")
            # Clone the source repository
            repo = git.Repo.clone_from(SOURCE_REPO_URL, temp_dir)

            # Path to the notebook in the cloned repo
            notebook_file = os.path.join(temp_dir, NOTEBOOK_PATH)
            print(f"📓 Executing notebook: {notebook_file}")

            # Create a cloud-compatible version of the notebook
            cloud_notebook_file = os.path.join(temp_dir, 'cloud_notebook.ipynb')
            create_cloud_compatible_notebook(notebook_file, cloud_notebook_file)

            # Execute the cloud-compatible notebook
            output_path = os.path.join(temp_dir, 'output.ipynb')

            # Parameters to inject for cloud execution
            current_year = datetime.now().year
            target_folder = f"{current_year}-cloud"

            parameters = {
                'LOCAL_EXECUTION': False,
                'GITHUB_TOKEN': '',  # Will be retrieved from Secret Manager
                'TARGET_REPO': TARGET_REPO,
                'TARGET_FOLDER': target_folder,
                'EXECUTION_ENVIRONMENT': 'Google Cloud Run',
                'CURRENT_YEAR': current_year
            }

            pm.execute_notebook(
                cloud_notebook_file,
                output_path,
                parameters=parameters
            )

            # Read the executed notebook
            with open(output_path, 'r') as f:
                nb = nbformat.read(f, as_version=4)

            # Convert to HTML for display
            html_exporter = HTMLExporter()
            html_data, resources = html_exporter.from_notebook_node(nb)

            print("✅ Notebook executed successfully")
            return {
                'status': 'success',
                'message': 'Notebook executed successfully'
            }
    except Exception as e:
        print(f"❌ Notebook execution failed: {e}")
        return {
            'status': 'error',
            'message': f'Notebook execution failed: {str(e)}'
        }

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

def execute_notebook_simulation():
    """Simulate notebook execution when dependencies are not available"""
    print("🔄 Simulating notebook execution (dependencies not available)")
    return {
        'status': 'success',
        'message': 'Notebook execution simulated successfully (install dependencies for full functionality)'
    }

@app.route('/run-notebook', methods=['POST'])
def run_notebook():
    try:
        print(f"[INFO] /run-notebook triggered", file=sys.stderr)
        payload = request.get_json(force=True, silent=True) or {}

        notebook_path = payload.get("notebook_path", NOTEBOOK_PATH)
        parameters = payload.get("parameters", {})
        print(f"[DEBUG] Received parameters: {json.dumps(parameters)}", file=sys.stderr)
        print(f"[DEBUG] Notebook path: {notebook_path}", file=sys.stderr)

        if not NOTEBOOK_EXECUTION_AVAILABLE:
            print("[WARN] Notebook execution dependencies missing", file=sys.stderr)
            return jsonify(execute_notebook_simulation())

        # Create a temporary working directory
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"[DEBUG] Cloning {SOURCE_REPO_URL} into {temp_dir}", file=sys.stderr)
            git.Repo.clone_from(SOURCE_REPO_URL, temp_dir)

            notebook_file = os.path.join(temp_dir, notebook_path)
            output_path = os.path.join(temp_dir, 'executed.ipynb')

            if not os.path.exists(notebook_file):
                raise FileNotFoundError(f"Notebook not found: {notebook_file}")

            print(f"[DEBUG] Executing notebook: {notebook_file}", file=sys.stderr)

            # Inject parameters and execute notebook
            try:
                pm.execute_notebook(
                    notebook_file,
                    output_path,
                    parameters=parameters
                )
                print("[DEBUG] Notebook executed", file=sys.stderr)
            except Exception as e:
                print(f"[ERROR] Execution failed: {e}", file=sys.stderr)
                return jsonify({'status': 'error', 'message': f"Execution failed: {str(e)}"}), 500

            # Export notebook to HTML
            try:
                with open(output_path, 'r') as f:
                    nb = nbformat.read(f, as_version=4)
                html_exporter = HTMLExporter()
                html_data, _ = html_exporter.from_notebook_node(nb)
                print(f"[DEBUG] Notebook HTML size: {len(html_data)} bytes", file=sys.stderr)
            except Exception as e:
                print(f"[WARN] HTML export failed: {e}", file=sys.stderr)

            return jsonify({
                'status': 'success',
                'message': 'Notebook executed successfully'
            })

    except Exception as e:
        print(f"[ERROR] /run-notebook error: {e}", file=sys.stderr)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle webhook from GitHub to update when the repo changes"""
    try:
        payload = request.json
        print(f"[DEBUG] Webhook payload: {json.dumps(payload)}", file=sys.stderr)

        if payload.get('ref') == 'refs/heads/main':
            subprocess.run(["git", "pull"], cwd="/app")
            print("[DEBUG] Git pull triggered", file=sys.stderr)
            return jsonify({'status': 'success'})
        return jsonify({'status': 'no action'})
    except Exception as e:
        print(f"[ERROR] Webhook handler failed: {e}", file=sys.stderr)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/status')
def status():
    """Show system status and available features"""
    return jsonify({
        'environment': 'local' if not CLOUD_AVAILABLE else 'cloud',
        'cloud_available': CLOUD_AVAILABLE,
        'notebook_execution_available': NOTEBOOK_EXECUTION_AVAILABLE,
        'github_token_configured': bool(os.environ.get('GITHUB_TOKEN')),
        'config': {
            'source_repo': SOURCE_REPO_URL,
            'target_repo': TARGET_REPO,
            'notebook_path': NOTEBOOK_PATH
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8100))

    print("🚀 Starting unified Flask server")
    print(f"🌐 Server URL: http://localhost:{port}")
    print(f"📱 Simple interface: http://localhost:{port}/")
    print(f"⚙️  Configuration: http://localhost:{port}/config")
    print(f"📊 System status: http://localhost:{port}/status")
    print()
    print("📋 System capabilities:")
    print(f"  • Google Cloud integration: {'✅' if CLOUD_AVAILABLE else '❌'}")
    print(f"  • Notebook execution: {'✅' if NOTEBOOK_EXECUTION_AVAILABLE else '❌'}")
    print(f"  • GitHub token configured: {'✅' if os.environ.get('GITHUB_TOKEN') else '❌'}")

    app.run(host='0.0.0.0', port=port, debug=True)

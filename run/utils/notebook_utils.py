import tempfile
import os
import git
import nbformat
from nbconvert import HTMLExporter
import papermill as pm

from utils.compat_utils import (
    create_local_compatible_notebook,
    create_cloud_compatible_notebook
)

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


def execute_notebook_simulation():
    """Simulate notebook execution when dependencies are not available"""
    print("🔄 Simulating notebook execution (dependencies not available)")
    return {
        'status': 'success',
        'message': 'Notebook execution simulated successfully (install dependencies for full functionality)'
    }

import os
import tempfile
import subprocess
import requests
import json
from flask import Flask, render_template, request, jsonify
from google.cloud import secretmanager
import git
import papermill as pm
import nbformat
from nbconvert import HTMLExporter

app = Flask(__name__)

# Configuration
SOURCE_REPO_URL = "https://github.com/username/source-repo.git"
TARGET_REPO = "datascape/RealityStream2025"
NOTEBOOK_PATH = "path/to/notebook.ipynb"

# Get the GitHub token from Secret Manager
def get_github_token():
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{os.environ.get('GOOGLE_CLOUD_PROJECT')}/secrets/github-token/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/run-notebook', methods=['POST'])
def run_notebook():
    try:
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Clone the source repository
            repo = git.Repo.clone_from(SOURCE_REPO_URL, temp_dir)
            
            # Path to the notebook in the cloned repo
            notebook_file = os.path.join(temp_dir, NOTEBOOK_PATH)
            
            # Execute the notebook
            output_path = os.path.join(temp_dir, 'output.ipynb')
            pm.execute_notebook(
                notebook_file,
                output_path,
                parameters={}
            )
            
            # Read the executed notebook
            with open(output_path, 'r') as f:
                nb = nbformat.read(f, as_version=4)
            
            # Convert to HTML for display
            html_exporter = HTMLExporter()
            html_data, resources = html_exporter.from_notebook_node(nb)
            
            # The notebook execution will trigger the upload_reports_to_github function
            # which is defined in the notebook itself
            
            return jsonify({
                'status': 'success',
                'message': 'Notebook executed successfully'
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle webhook from GitHub to update when the repo changes"""
    try:
        payload = request.json
        if 'ref' in payload and payload['ref'] == 'refs/heads/main':
            # Pull the latest changes
            subprocess.run(["git", "pull"], cwd="/app")
            return jsonify({'status': 'success'})
        return jsonify({'status': 'no action'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
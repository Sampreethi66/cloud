import os
import sys
import tempfile
import subprocess
import requests
import json
import yaml
from flask import Flask, render_template, request, jsonify
from google.cloud import secretmanager
import git
import papermill as pm
import nbformat
from nbconvert import HTMLExporter

app = Flask(__name__)

# Load configuration from config.yaml
def load_config():
    try:
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        # Fallback configuration if config.yaml doesn't exist
        return {
            'github': {
                'source_repo_url': 'https://github.com/AbhinavSivanandhan/cloud.git',
                'target_repo': 'https://github.com/AbhinavSivanandhan/reports.git',
                'notebook_path': 'run/notebook.ipynb'
            }
        }

config = load_config()
SOURCE_REPO_URL = config['github']['source_repo_url']
TARGET_REPO = config['github']['target_repo']
NOTEBOOK_PATH = config['github']['notebook_path']

# Get the GitHub token from Secret Manager
def get_github_token():
    try:
        client = secretmanager.SecretManagerServiceClient()
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
        print(f"[DEBUG] Project ID for Secret Manager: {project_id}", file=sys.stderr)
        name = f"projects/{project_id}/secrets/github-token/versions/latest"
        response = client.access_secret_version(request={"name": name})
        token = response.payload.data.decode("UTF-8")
        print(f"[DEBUG] GitHub token fetched successfully. Token length: {len(token)}", file=sys.stderr)
        return token
    except Exception as e:
        print(f"[ERROR] Failed to access GitHub token from Secret Manager: {e}", file=sys.stderr)
        return None

@app.route('/')
def home():
    try:
        with open('page.html', 'r') as f:
            return f.read()
    except Exception as e:
        print(f"[ERROR] Failed to load page.html: {e}", file=sys.stderr)
        return "<h2>Error loading homepage</h2>", 500

@app.route('/run-notebook', methods=['POST'])
def run_notebook():
    try:
        print(f"[INFO] Triggered /run-notebook", file=sys.stderr)

        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"[DEBUG] Created temp dir: {temp_dir}", file=sys.stderr)

            # Clone the source repository
            print(f"[DEBUG] Cloning from repo: {SOURCE_REPO_URL}", file=sys.stderr)
            repo = git.Repo.clone_from(SOURCE_REPO_URL, temp_dir)

            # Path to the notebook in the cloned repo
            notebook_file = os.path.join(temp_dir, NOTEBOOK_PATH)
            print(f"[DEBUG] Notebook file path: {notebook_file}", file=sys.stderr)

            # Execute the notebook
            output_path = os.path.join(temp_dir, 'output.ipynb')
            print(f"[DEBUG] Executing notebook → Output path: {output_path}", file=sys.stderr)

            pm.execute_notebook(
                notebook_file,
                output_path,
                parameters={}
            )

            print(f"[DEBUG] Notebook executed successfully", file=sys.stderr)

            # Read the executed notebook
            with open(output_path, 'r') as f:
                nb = nbformat.read(f, as_version=4)

            # Convert to HTML for display
            html_exporter = HTMLExporter()
            html_data, resources = html_exporter.from_notebook_node(nb)
            print(f"[DEBUG] Converted notebook to HTML. Length: {len(html_data)} bytes", file=sys.stderr)

            # The notebook execution will trigger the upload_reports_to_github function
            # which is defined in the notebook itself

            return jsonify({
                'status': 'success',
                'message': 'Notebook executed successfully'
            })

    except Exception as e:
        print(f"[ERROR] Exception in /run-notebook: {e}", file=sys.stderr)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle webhook from GitHub to update when the repo changes"""
    try:
        payload = request.json
        print(f"[DEBUG] Webhook payload received: {json.dumps(payload)}", file=sys.stderr)

        if 'ref' in payload and payload['ref'] == 'refs/heads/main':
            # Pull the latest changes
            subprocess.run(["git", "pull"], cwd="/app")
            print("[DEBUG] Repo updated via webhook", file=sys.stderr)
            return jsonify({'status': 'success'})
        return jsonify({'status': 'no action'})
    except Exception as e:
        print(f"[ERROR] Exception in webhook handler: {e}", file=sys.stderr)
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"[INFO] Starting app on port {port}", file=sys.stderr)
    app.run(host='0.0.0.0', port=port)

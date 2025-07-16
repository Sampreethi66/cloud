import os
import sys
import tempfile
import subprocess
import requests
import json
import yaml
from flask import Flask, request, jsonify
from google.cloud import secretmanager
import git
import papermill as pm
import nbformat
from nbconvert import HTMLExporter

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
DEFAULT_NOTEBOOK_PATH = config['github']['notebook_path']

# === Retrieve GitHub token from Secret Manager ===
def get_github_token():
    try:
        client = secretmanager.SecretManagerServiceClient()
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
        name = f"projects/{project_id}/secrets/github-token/versions/latest"
        response = client.access_secret_version(request={"name": name})
        token = response.payload.data.decode("UTF-8")
        print(f"[DEBUG] GitHub token retrieved. Length: {len(token)}", file=sys.stderr)
        return token
    except Exception as e:
        print(f"[ERROR] Secret Manager error: {e}", file=sys.stderr)
        return None

@app.route('/')
def home():
    try:
        with open('page.html', 'r') as f:
            return f.read()
    except Exception as e:
        print(f"[ERROR] Failed to load homepage: {e}", file=sys.stderr)
        return "<h2>Error loading homepage</h2>", 500

@app.route('/run-notebook', methods=['POST'])
def run_notebook():
    try:
        print(f"[INFO] /run-notebook triggered", file=sys.stderr)
        payload = request.get_json(force=True, silent=True) or {}
        notebook_path = payload.get("notebook_path", DEFAULT_NOTEBOOK_PATH)
        parameters = payload.get("parameters", {})
        print(f"[DEBUG] Received parameters: {json.dumps(parameters)}", file=sys.stderr)

        # Create a temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"[DEBUG] Cloning {SOURCE_REPO_URL} into {temp_dir}", file=sys.stderr)
            git.Repo.clone_from(SOURCE_REPO_URL, temp_dir)

            notebook_file = os.path.join(temp_dir, notebook_path)
            output_path = os.path.join(temp_dir, 'executed.ipynb')

            if not os.path.exists(notebook_file):
                raise FileNotFoundError(f"Notebook not found: {notebook_file}")

            print(f"[DEBUG] Executing notebook: {notebook_path}", file=sys.stderr)

            try:
                pm.execute_notebook(
                    notebook_file,
                    output_path,
                    parameters=parameters
                )
                print(f"[DEBUG] Notebook executed", file=sys.stderr)
            except Exception as e:
                print(f"[ERROR] Notebook execution failed: {e}", file=sys.stderr)
                return jsonify({'status': 'error', 'message': f"Execution failed: {str(e)}"}), 500

            # convert notebook to HTML for local viewing/debugging
            try:
                with open(output_path, 'r') as f:
                    nb = nbformat.read(f, as_version=4)
                html_exporter = HTMLExporter()
                html_data, _ = html_exporter.from_notebook_node(nb)
                print(f"[DEBUG] Notebook HTML size: {len(html_data)} bytes", file=sys.stderr)
            except Exception as e:
                print(f"[WARN] Failed to convert notebook to HTML: {e}", file=sys.stderr)

            # Upload is handled by the notebook itself
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"[INFO] Flask app running on port {port}", file=sys.stderr)
    app.run(host='0.0.0.0', port=port)

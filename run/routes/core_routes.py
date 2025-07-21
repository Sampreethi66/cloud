from flask import Blueprint, request, jsonify
from utils.config_utils import load_config, save_config
from utils.github_utils import get_github_token
import nbformat

core_blueprint = Blueprint('core', __name__)

@core_blueprint.route('/')
def home():
    try:
        with open('page.html', 'r') as f:
            return f.read()
    except Exception as e:
        print(f"[ERROR] Failed to load homepage: {e}", file=sys.stderr)
        return "<h2>Error loading homepage</h2>", 500

@core_blueprint.route('/config')
def config_page():
    with open('index.html', 'r') as f:
        return f.read()

@core_blueprint.route('/get-config', methods=['GET'])
def get_config_route():
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

@core_blueprint.route('/save-config', methods=['POST'])
def save_config_route():
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

@core_blueprint.route('/status')
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

@core_blueprint.route('/webhook', methods=['POST'])
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

@app.route('/list-notebook-steps', methods=['GET'])
def list_notebook_steps():
    try:
        notebook_path = 'notebook.ipynb'  # update if path is different
        with open(notebook_path, 'r', encoding='utf-8') as f:
            nb = nbformat.read(f, as_version=4)

        steps = []
        for cell in nb.cells:
            tags = cell.get('metadata', {}).get('tags', [])
            for tag in tags:
                if tag.startswith('step:'):
                    step_name = tag.split('step:')[1]
                    if step_name not in steps:
                        steps.append(step_name)

        return jsonify({'status': 'success', 'steps': steps})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

from flask import Blueprint, request, jsonify
import sys, os, json, tempfile, nbformat, git
from nbconvert import HTMLExporter
import papermill as pm
import traceback
from utils.config_utils import load_config
from utils.notebook_utils import (
    NOTEBOOK_PATH,
    SOURCE_REPO_URL,
    TARGET_REPO,
    execute_notebook_with_dependencies,
    execute_notebook_cloud,
    execute_notebook_simulation,
    NOTEBOOK_EXECUTION_AVAILABLE
)


notebook_blueprint = Blueprint('notebook', __name__)

@notebook_blueprint.route('/run-notebook', methods=['POST'])
def run_notebook():
    try:
        print(f"[INFO] /run-notebook triggered", file=sys.stderr)
        payload = request.get_json(force=True, silent=True) or {}

        notebook_path = payload.get("notebook_path", NOTEBOOK_PATH)
        parameters = payload.get("parameters", {})
        steps = payload.get("steps", [])  # Optional, empty by default
        if steps:
            parameters['steps'] = steps  # Inject into notebook if provided
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

@notebook_blueprint.route('/list-notebook-steps', methods=['GET'])
def list_notebook_steps():
    import traceback
    try:
        print("[INFO] /list-notebook-steps triggered", file=sys.stderr)
        print(f"[DEBUG] NOTEBOOK_PATH: {NOTEBOOK_PATH}", file=sys.stderr)

        # Clone the repo into a temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"[DEBUG] Cloning {SOURCE_REPO_URL} into {temp_dir}", file=sys.stderr)
            git.Repo.clone_from(SOURCE_REPO_URL, temp_dir)

            notebook_file = os.path.join(temp_dir, NOTEBOOK_PATH)
            if not os.path.exists(notebook_file):
                raise FileNotFoundError(f"Notebook not found at: {notebook_file}")

            print(f"[DEBUG] Parsing notebook for step tags: {notebook_file}", file=sys.stderr)
            with open(notebook_file, 'r') as f:
                nb = nbformat.read(f, as_version=4)

            # Extract step tags like 'step:xyz'
            step_tags = set()
            for cell in nb.cells:
                tags = cell.metadata.get("tags", [])
                for tag in tags:
                    if tag.startswith("step:"):
                        step_tags.add(tag.split("step:")[1])

            print(f"[DEBUG] Steps found: {step_tags}", file=sys.stderr)
            return jsonify({
                "status": "success",
                "steps": sorted(step_tags)
            })

    except Exception as e:
        print("[ERROR] Exception in /list-notebook-steps", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

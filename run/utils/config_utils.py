import os
import yaml

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
    config_path = os.path.abspath(config_path)

    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"[WARN] Config not found at {config_path}, using defaults.")
        return {
            'github': {
                'source_repo_url': 'https://github.com/AbhinavSivanandhan/cloud.git',
                'target_repo': 'https://github.com/AbhinavSivanandhan/reports.git',
                'notebook_path': 'run/notebook.ipynb'
            }
        }

def save_config(config):
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
    config_path = os.path.abspath(config_path)
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)

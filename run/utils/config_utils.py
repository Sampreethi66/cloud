import yaml

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

def save_config(config):
    with open('config.yaml', 'w') as f:
        yaml.dump(config, f, default_flow_style=False)

import json

def read_config(config_path):
    config_data = None
    with open(config_path, 'r') as f:
        config_data = json.load(f)
    return config_data

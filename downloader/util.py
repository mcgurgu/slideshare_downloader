import json
import os


def read_config(key):
    config_path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(config_path, 'config.json'), 'r') as f:
        return json.load(f)[key]

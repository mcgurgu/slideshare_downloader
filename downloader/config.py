import json
import os

# How to write a static python getitem method?: http://stackoverflow.com/q/6187932/1432478
class MetaConfig(type):
    def __getitem__(cls, key):
        return str(Config.config[key])


class Config:
    __metaclass__ = MetaConfig
    config = None

    _config_path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(_config_path, 'config.json'), 'r') as f:
        config = json.load(f)

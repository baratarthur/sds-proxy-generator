import json

class DidlReader:
    def __init__(self, json_path, remote_pods: int = 2):
        didl_config = json.load(json_path)
        self.dependencies = didl_config['dependencies']
        self.attributes = didl_config['attributes']  if 'attributes' in didl_config else {}
        self.methods = didl_config['methods']
        self.remote_pods = remote_pods
        self.remote_name = didl_config.get('name', 'dana-remote')

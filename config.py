import json

class DidlReader:
    def __init__(self, json_path, remote_pods: int = 2):
        didl_config = json.load(json_path)
        self.dependencies = didl_config['dependencies']
        self.attributes = didl_config['attributes']  if 'attributes' in didl_config else {}
        self.methods = didl_config['methods']
        self.remote_pods = remote_pods
        self.remote_name = didl_config.get('remoteName', 'dana-remote')
    
    def calculate_on_active(self, strategy: str, type: str) -> list:
        instructions = [
            # f'remotes = podCreator.getPodsName(Constants.NUMBER_OF_REMOTES, \"{self.remote_name}-{strategy}-{type}\")'
        ]
        for attribute in self.attributes:
            if 'calculateWith' in self.attributes[attribute]:
                instructions.append(f"{self.attributes[attribute]['calculateWith']}({attribute})")
            elif 'calculateWithEach' in self.attributes[attribute]:
                instructions.append(f"for(int i = 0; i < {attribute}.arrayLength; i++)" + "{")
                instructions.append(f"\t{self.attributes[attribute]['calculateWithEach']}({attribute}[i])")
                instructions.append("}")
        return instructions

    def calculate_on_inactive(self) -> list:
        instructions = []
        for attribute in self.attributes:
            instructions.append(f"{attribute} = get{attribute[0].upper() + attribute[1:]}()")
        # instructions.append("podCreator.deleteAllPods(remotes)")
        return instructions

from helpers.write_component_helper import WriteComponentHelper

class AdaptationGenerator:
    def __init__(self, writer: WriteComponentHelper, strategy: str = None, type: str = None):
        self.writer = writer
        self.strategy = strategy
        self.type = type

    def provide_on_load_remote_state(self):
        return self.writer.provide_idented_flow("bool AdaptationLyfecicle:onLoadRemoteState()", self.calculate_on_load_remote_state())
    
    def provide_on_update_local_state(self):
        return self.writer.provide_idented_flow("bool AdaptationLyfecicle:onUpdateLocalState()", self.calculate_on_update_local_state())
    
    def calculate_on_load_remote_state(self) -> list:
        instructions = []
        instructions.append("return true")
        return instructions

    def calculate_on_update_local_state(self) -> list:
        instructions = [
            'char requestBody[] = ""',
			'Request req = new Request(buildMetaForMethod("clearState"), requestBody)'
			'broadcast(req)'
        ]
        instructions.append("return true")
        return instructions
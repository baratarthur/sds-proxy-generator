from helpers.write_component_helper import WriteComponentHelper

class AdaptationGenerator:
    def __init__(self, writer: WriteComponentHelper, attributes, strategy: str = None, type: str = None):
        self.writer = writer
        self.strategy = strategy
        self.type = type
        self.attributes = attributes

    def provide_on_load_remote_state(self):
        return self.writer.provide_idented_flow("bool AdaptationLyfecicle:onLoadRemoteState()", self.calculate_on_load_remote_state())
    
    def provide_on_update_local_state(self):
        return self.writer.provide_idented_flow("bool AdaptationLyfecicle:onUpdateLocalState()", self.calculate_on_update_local_state())
    
    def calculate_on_load_remote_state(self) -> list:
        instructions = []
        for attribute in self.attributes: instructions.append(f"{self.attributes[attribute]['onTransfer']}({attribute})")
        instructions.append("return true")
        return instructions

    def calculate_on_update_local_state(self) -> list:
        instructions = []
        for attribute in self.attributes: instructions.append(f"{attribute} = {self.attributes[attribute]['onLoad']}()")
        instructions.append("return true")
        return instructions
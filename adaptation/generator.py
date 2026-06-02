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
        # for attribute in self.attributes:
        #     if 'calculateWith' in self.attributes[attribute]:
        #         instructions.append(f"{self.attributes[attribute]['calculateWith']}({attribute})")
        #     elif 'calculateWithEach' in self.attributes[attribute]:
        #         instructions.append(f"for(int i = 0; i < {attribute}.arrayLength; i++)" + "{")
        #         instructions.append(f"\t{self.attributes[attribute]['calculateWithEach']}({attribute}[i])")
        #         instructions.append("}")
        instructions.append("return true")
        return instructions

    def calculate_on_update_local_state(self) -> list:
        instructions = []
        # for attribute in self.attributes:
        #     instructions.append(f"{attribute} = get{attribute[0].upper() + attribute[1:]}()")
        instructions.append("return true")
        return instructions
from helpers.write_component_helper import WriteComponentHelper

class AdaptationGenerator:
    def __init__(self, writer: WriteComponentHelper, on_active: list, on_inactive: list):
        self.writer = writer
        self.on_active = on_active
        self.on_inactive = on_inactive

    def provide_on_active(self):
        return self.writer.provide_idented_flow("void AdaptEvents:active()", self.on_active)

    def provide_on_inactive(self):
        return self.writer.provide_idented_flow("void AdaptEvents:inactive()", self.on_inactive)
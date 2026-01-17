from helpers.write_component_helper import WriteComponentHelper

class HeaderGenerator:
    def __init__(self, interface_file_path, dependencies):
        self.name = self.get_component_name(interface_file_path)
        self.general_dependencies = self.provide_general_dependecies(dependencies)
        self.component_dependencies = self.provide_component_dependecies(dependencies)

    def get_component_name(self, interface_file_path) -> str:
        return interface_file_path.replace("resources/", "").replace(".dn", "").replace("/", ".")

    def get_component_flow(self, writer: WriteComponentHelper):
        writer.write_idented(self.general_dependencies)
        writer.break_line()

        return writer.use_idented_flow(f"component provides {self.name}(AdaptEvents) {self.get_component_definition()}")

    def get_component_definition(self) -> str:
        return "requires " + self.component_dependencies if self.component_dependencies != "" else ""
    
    def provide_general_dependecies(self, dependencies) -> str:
        return "".join([f"uses {dep['lib']}\n" for dep in dependencies if dep['alias'] == None])
    
    def provide_component_dependecies(self, dependencies) -> str:
        return ", ".join([f"{dep['lib']} {dep['alias']}" for dep in dependencies if dep['alias'] != None])
    
    def static_provide_component_dependecies(dependencies) -> str:
        return ", ".join([f"{dep['lib']} {dep['alias']}" for dep in dependencies if dep['alias'] != None])
    
    def provide_addresses(self) -> str:
        var_assign = f"Address remotes[] = new Address[]"
        return var_assign
    
    def provide_pointer(self) -> list:
        return ["int addressPointer = 0", "Mutex pointerLock = new Mutex()"]
    
    def get_interface_name(self) -> str:
        return self.name.split('.')[-1]

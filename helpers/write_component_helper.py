
def use_identation(func):
    def identation_wrapper(self, *args, **kwargs):
        self.ident()
        func(self, *args, **kwargs)
        self.break_line()
    return identation_wrapper

def use_flow(flow: str):
    def use_flow_dec(func):
        def flow_wrapper(self, *args, **kwargs):
            self.ident()
            self.file.write(flow)
            self.file.write(" {")
            self.break_line()
            self.improve_identation_level()
            func(self, *args, **kwargs)
            self.close_component()
        return flow_wrapper
    return use_flow_dec

class WriteComponentHelper:
    def __init__(self, file, identation_level=0):
        self.identation_level = identation_level
        self.file = file

    @use_identation
    def write_idented(self, line: str):
        self.file.write(line)
    
    def provide_idented_flow(self, flow: str, lines: list):
        @use_flow(flow)
        def flow_writer(self):
            for line in lines:
                if line is None:
                    pass
                elif isinstance(line, str):
                    self.write_idented(line)
                else:
                    line(self)
        return flow_writer

    def use_idented_flow(self, flow: str):
        @use_flow(flow)
        def flow_writer(self, lines: list):
            for line in lines:
                if line is None:
                    pass
                elif isinstance(line, str):
                    self.write_idented(line)
                else:
                    line(self)
        return flow_writer

    def ident(self):
        self.file.write(self.identation_level * "\t")

    def improve_identation_level(self):
        self.identation_level += 1

    def deteriorate_identation_level(self):
        self.identation_level -= 1

    def break_line(self):
        self.file.write("\n")

    def close_component(self):
        self.deteriorate_identation_level()
        self.ident()
        self.file.write("}")
        self.break_line()
        self.break_line()
    
    

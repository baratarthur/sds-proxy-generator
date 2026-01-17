from helpers.write_component_helper import WriteComponentHelper

replicated_strategies = ['distribute']

class RemoteGenerator:
    def __init__(self, file, component_name, component_package, component_deps,
                 component_methods, connection_library="network.rpc.RPCUtil connection"):
        self.writer = WriteComponentHelper(file)
        self.component_name = component_name
        self.component_package = component_package
        self.component_methods = component_methods
        self.resources = [
            "net.TCPSocket",
            "net.TCPServerSocket",
            "io.Output out",
            "data.json.JSONEncoder je",
            component_deps,
            connection_library,
            f"{component_package}.{component_name[0].upper() + component_name[1:]} remoteComponent",
        ]
    
    def provide_header(self):
        self.writer.write_idented("uses utils.Constants")
        self.writer.break_line()
        self.writer.write_idented('const char debugMSG[] = "[@Remote]"')
        self.writer.break_line()
        self.writer.break_line()

    def provide_component_resources(self):
        return "requires " + ", ".join(self.resources)

    def provide_server_methods(self):
        inside_component = self.writer.use_idented_flow(f"component provides remotes.Remote:{self.component_name.lower()} {self.provide_component_resources()}")
        
        inside_component(self.writer, [
            "bool serviceStatus = false",
            "\n",
            self.provie_init_method(),
            self.provide_handle_request(),
            self.provide_processing_method(),
        ])

    def provie_init_method(self):
        return self.writer.provide_idented_flow("void Remote:start(int PORT)", [
            "TCPServerSocket host = new TCPServerSocket()",
            "serviceStatus = true",
            "\n",
            self.writer.provide_idented_flow("if (!host.bind(TCPServerSocket.ANY_ADDRESS, PORT))", [
                'out.println("Error: failed to bind master socket")',
                "return"
            ]),
            'out.println("$debugMSG - Server started on port $(iu.makeString(PORT))")',
            self.writer.provide_idented_flow("while (serviceStatus)", [
                "TCPSocket client = new TCPSocket()",
                "if (client.accept(host)) asynch::handleRequest(client)"
            ])
        ])

    def provide_handle_request(self):
        return self.writer.provide_idented_flow("void Remote:handleRequest(TCPSocket s)", [
            "char requestContent[] = connection.receiveData(s)",
            "if(requestContent == null) s.disconnect()",
            "Request req = connection.parseRequestFromString(requestContent)",
            "Response res = process(req)",
            "char rawResponse[] = connection.buildRawResponse(res)",
            "s.send(rawResponse)",
            "s.disconnect()",
        ])

    def provide_processing_method(self):
        strategies_provider = [
            "char method[] = connection.getMethodFromMetadata(req.meta)",
            "\n",
        ]

        for method in self.component_methods:
            strategies_provider.append(
                self.writer.provide_idented_flow(f'if(method == "{method}")',[
                    self.converted_params(method),
                    self.remote_function_call(method),
                    self.return_value(method)
                ])
            )
        strategies_provider.append('return connection.buildResponse(method, "404")')

        return self.writer.provide_idented_flow("Response process(Request req)", strategies_provider)
    
    def converted_params(self, method) -> str:
        method_configs = self.component_methods[method]
        has_params = len(method_configs['parameters']) > 0
        parameters_format_type = f"{method[0].upper() + method[1:]}ParamsFormat"
        return f"{parameters_format_type} paramsData = je.jsonToData(req.content, typeof({parameters_format_type}))" if has_params else None
    
    def remote_function_call(self, method) -> str:
        method_configs = self.component_methods[method]
        has_params = len(method_configs['parameters']) > 0
        is_collection_result = '[]' in method_configs['returnType']
        should_return_data = 'remoteReturnParser' in method_configs

        store_result = f"{method_configs['returnType'].replace('[]', '') if is_collection_result else method_configs['returnType']} result{'[]' if is_collection_result else ''} = "
        return f"{store_result if should_return_data else ''}remoteComponent.{method}({self.provide_virables_for_method(method_configs) if has_params else ''})"
    
    def return_value(self, method) -> str:
        method_configs = self.component_methods[method]
        should_return_data = 'remoteReturnParser' in method_configs

        return f'return connection.{"buildResponseWithData" if should_return_data else "buildResponse"}("{method}", "200"{", " + method_configs["remoteReturnParser"].format("result") if should_return_data else ""})'

    def provide_virables_for_method(self, method_config) -> str:
        def get_formated_parser(param):
            should_parse_variable = 'variableParser' in param
            return param['variableParser'].format(f"paramsData.{param['name']}") if should_parse_variable else f"paramsData.{param['name']}"

        return ",".join([f"{get_formated_parser(param)}" for param in method_config['parameters']])    

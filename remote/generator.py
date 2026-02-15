from helpers.write_component_helper import WriteComponentHelper
from helpers.extract_helper import extract_method_information_from_interface

replicated_strategies = ['distribute']

class RemoteGenerator:
    def __init__(self, file, component_name, component_package, component_deps,
                 component_methods, interface_definitions, connection_library="libs.network.rpc.RPCUtil connection"):
        self.writer = WriteComponentHelper(file)
        self.component_name = component_name
        self.component_package = component_package
        self.component_methods = component_methods
        self.methods_information = extract_method_information_from_interface(interface_definitions)
        self.resources = [
            "net.TCPSocket",
            "net.TCPServerSocket",
            "io.Output out",
            "data.IntUtil iu",
            "data.json.JSONEncoder je",
            component_deps,
            connection_library,
            f"{component_package}.{component_name[0].upper() + component_name[1:]} remoteComponent",
        ]
    
    def provide_header(self):
        self.writer.write_idented("uses libs.utils.Constants")
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

        method_names = [method['method'] for method in self.methods_information]

        for method in method_names:
            strategies_provider.append(
                self.writer.provide_idented_flow(f'if(method == "{method}")',[
                    self.converted_params(method),
                    self.function_call(method),
                    self.return_value(method)
                ])
            )
        strategies_provider.append('return connection.buildResponse(method, "404")')

        return self.writer.provide_idented_flow("Response process(Request req)", strategies_provider)
    
    def converted_params(self, method) -> str:
        method_infos = next((info for info in self.methods_information if info['method'] == method), None)
        have_params = len(method_infos['parameters']) > 0
        parameters_format_type = f"{method[0].upper() + method[1:]}ParamsFormat"
        return f"{parameters_format_type} paramsData = je.jsonToData(req.content, typeof({parameters_format_type}))" if have_params else None
    
    def function_call(self, method) -> str:
        method_infos = next((info for info in self.methods_information if info['method'] == method), None)
        is_collection_result = '[]' in method_infos['return_type']
        should_return_data = method_infos['return_type'] != 'void'

        store_result = f"{method_infos['return_type'].replace('[]', '') if is_collection_result else method_infos['return_type']} result{'[]' if is_collection_result else ''} = "
        return f"{store_result if should_return_data else ''}remoteComponent.{method}({self.provide_virables_for_method(method_infos)})"
    
    def return_value(self, method) -> str:
        method_config = self.component_methods[method] if method in self.component_methods else {}
        method_infos = next((info for info in self.methods_information if info['method'] == method), None)
        should_return_data = method_infos['return_type'] != 'void'

        return f'return connection.{"buildResponseWithData" if should_return_data else "buildResponse"}("{method}", "200"{", " + method_config["remoteReturnParser"].format("result") if should_return_data else ""})'

    def provide_virables_for_method(self, method_config) -> str:
        return ",".join([f"paramsData.{param.split(' ')[-1].replace('[]', '')}" for param in method_config['parameters']])    

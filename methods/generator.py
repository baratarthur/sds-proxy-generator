import regex
import re
from helpers.extract_helper import extract_method_information_from_interface
from helpers.write_component_helper import WriteComponentHelper
from strategy.configs import strategy_configs
from methods.config import special_methods

class MethodsGenerator:
    def __init__(self, methods, interface_name, attributes, component_implementations, interface_definitions, startegy):
        self.methods = methods
        self.interface_name = interface_name
        self.attributes = attributes
        self.component_implementations = component_implementations
        self.interface_definitions = interface_definitions
        self.strategy = startegy
        self.distribution_configs = strategy_configs[startegy]

    def provide_method_implementation(self, writer):
        return self.provide_methods(writer)

    def provide_methods(self, writer: WriteComponentHelper, strategy: str):
        methods = [
            writer.provide_idented_flow('Metadata[] buildMetaForMethod(char method[])', [
                'Metadata metaMethod = new Metadata("method", method)',
                'return new Metadata[](metaMethod)',
            ])
        ]

        methods_information = extract_method_information_from_interface(self.interface_definitions)
        method_names = [method['method'] for method in methods_information]

        # print("method information: ", methods_information)

        for method in method_names:
            method_props = self.methods[method] if method in self.methods else {}
            method_infos = next((info for info in methods_information if info['method'] == method), None)
            builder = MethodBuilder(method, method_props, method_infos)

            escaped_return_type = re.escape(method_infos['return_type'])
            escaped_interface = re.escape(self.interface_name)
            escaped_method = re.escape(method)

            header = (
                rf"{escaped_return_type}\s+{escaped_interface}:{escaped_method}\([^)]*\)\s*"
            )
            pattern = rf"{header}(?P<bodycontent>\{{(?:[^{{}}]++|(?&bodycontent))*\}})"
            method_implementation_code = regex.search(pattern, self.component_implementations).group(0)

            # se o método não altera o estado, o proxy deve apenas repassar a chamada da aplicação com base na carga

            method_changes_state = 0
            method_reads_state = 0

            for attribute in self.attributes:
                assignment_pattern = re.compile(fr"""
                    ^
                    .*?
                    \s*
                    \b{re.escape(attribute)}\b
                    \s*
                    (
                        \+= | -= | \*= | /= |
                        =(?!=)
                    )
                    .*
                """, re.VERBOSE)

                lines_with_state_change = []
                for line in method_implementation_code.split('\n'):
                    if line.strip().startswith("//"): continue
                    if assignment_pattern.match(line):
                        lines_with_state_change.append(line)
                    if attribute in line and not assignment_pattern.match(line):
                        variable_in_string = re.compile(r'"(?:\\.|[^"\\])*\b' + attribute + r'\b(?:\\.|[^"\\])*"', re.VERBOSE)
                        variable_used_in_string = re.compile(r"\$(?:\(" + attribute + r"\)|" + attribute + r"\b)", re.VERBOSE)
                        
                        if not variable_in_string.findall(line) and attribute in line:
                            method_reads_state += 1
                        elif variable_in_string.findall(line) and variable_used_in_string.match(line):
                            method_reads_state += 1

                if len(lines_with_state_change) > 0: method_changes_state += 1

            distribution_type = "no_state"
            if strategy == 'replicate':
                if method_changes_state > 0: distribution_type = "write"
                elif method_reads_state > 0: distribution_type = "read"
            elif strategy == 'fragment':
                if 'global' in method_props and method_props['global'] == True: distribution_type = "global"
                elif method_changes_state > 0:
                    if "balance" in method_props: distribution_type = "write_many"
                    else: distribution_type = "write_one"
                elif method_reads_state > 0:
                    if "dontMerge" in method_props and method_props["dontMerge"] == True: distribution_type = "no_state"
                    elif "onMerge" in method_props: distribution_type = "read_many"
                    else: distribution_type = "read_one"

            method_header = f"{method_infos['return_type']} {self.interface_name}:{method}({', '.join(method_infos['parameters'])})"
            have_params = len(method_infos['parameters']) > 0
            should_return_value = method_infos['return_type'] != 'void'

            print(f"Method: {method}, changes state: {method_changes_state > 0}, reads state: {method_reads_state > 0}, distribution type: {distribution_type}")

            if strategy == "fragment" and ("onMerge" in method_props or "balance" in method_props): # didl indications of n changes at the same time
                '''
                ===========================================================================
                Combine
                ===========================================================================
                Response responses[] = broadcastList(req)
                Post returnValue[]
                for(int i = 0; i < responses.arrayLength; i++) {
                    Post partialPost[] = je.jsonToArray(responses[i].content, typeof(Post[]))
                    returnValue = accummulate(returnValue, partialPost)
                }
                return returnValue
                ===========================================================================
                Split (considering void)
                ===========================================================================
                int spaceSize = remotes.arrayLength
                for(int i = 0; i < spaceSize; i++) {
                    Post subset[] = new Post[]()
                
                    for(int j = 0; j < posts.arrayLength; j++) {
                        if(posts[j].id % spaceSize == i ) {
                            subset = new Post[](subset, posts[j])
                        }
                    }

                    FunctionParamsFormat params = new FunctionParamsFormat(subset)
                    char requestBody[] = je.jsonFromArray(params)
                    Request req = new Request((buildMetaForMethod(\"{method}\"), requestBody)
                    hashcast(req, i)
                }

                '''

                if "onMerge" in method_props:
                    clear_method_type = method_infos['return_type'].replace("[]", "")
                    methods.append(writer.provide_idented_flow(method_header, [
                        # "DateTime timeBeforeParamsPack = ic.getTime()",
                        builder.generate_params_packing() if have_params else None,
                        # "int timeToProcessParamsPack = ls.getMilisecondsExecutionTimeSince(timeBeforeParamsPack)",
                        "char requestBody[] = je.jsonFromData(params)" if have_params else 'char requestBody[] = ""',
                        # "DateTime timeBeforeRequestMount = ic.getTime()",
                        f"Request req = new Request(buildMetaForMethod(\"{method}\"), requestBody)",
                        # "int timeToProcessRequestMount = ls.getMilisecondsExecutionTimeSince(timeBeforeRequestMount)",
                        # broadcast
                        # "DateTime timeBeforeRPC = ic.getTime()",
                        f"Response res[] = {strategy_configs[strategy]['methods'][distribution_type][1]}(req)",
                        # "int timeToProcessRPC = ls.getMilisecondsExecutionTimeSince(timeBeforeRPC)",
                        # combine
                        # "DateTime timeBeforeCombine = ic.getTime()",
                        f"{clear_method_type} returnValue[]",
                        writer.provide_idented_flow("for(int i = 0; i < res.arrayLength; i++)", [
                            f"{clear_method_type} partialValue[] = je.jsonToArray(res[i].content, typeof({clear_method_type}[]))",
                            f"returnValue = {method_props['onMerge']}(returnValue, partialValue)"
                        ]),
                        # "int timeToProcessCombine = ls.getMilisecondsExecutionTimeSince(timeBeforeCombine)",
                        # 'logger.storeInfo("{\\"timeToProcessParamsPack\\": \\"$(iu.makeString(timeToProcessParamsPack))\\", \\"timeToProcessRequestMount\\": \\"$(iu.makeString(timeToProcessRequestMount))\\", \\"timeToProcessRPC\\": \\"$(iu.makeString(timeToProcessRPC))\\", \\"timeToProcessCombine\\": \\"$(iu.makeString(timeToProcessCombine))\\"}")',
                        "return returnValue"
                    ]))

                elif "balance" in method_props: # consider only one prop
                    _, param_type, _ = MethodBuilder.get_meta_from(list(filter(lambda p: p.split()[2].replace('[]', '') == method_props['balance'], method_infos['parameters']))[0])
                    param_name = method_props['balance']
                    hashkey = method_props['hashkey']
                    methods.append(writer.provide_idented_flow(method_header, [
                        "int spaceSize = remotes.arrayLength",
                        writer.provide_idented_flow("for(int i = 0; i < spaceSize; i++)", [
                            f"{param_type} subset[] = new {param_type}[]()",
                            writer.provide_idented_flow(f"for(int j = 0; j < {param_name}.arrayLength; j++)", [
                                writer.provide_idented_flow(f"if({param_name}[j].{hashkey} % spaceSize == i)", [
                                   f"subset = new {param_type}[](subset, {param_name}[j])"
                                ]),
                            ]),
                            builder.generate_special_packing("subset"),
                            "char requestBody[] = je.jsonFromData(params)",
                            f"Request req = new Request(buildMetaForMethod(\"{method}\"), requestBody)",
                            f"{strategy_configs[strategy]['methods'][distribution_type][1]}(req, i)"
                        ]),
                    ]))
            else:
                '''
                Response res = anycast(req)
                return je.jsonToArray(res.content, typeof(Post[]))
                '''
                remote_execution_type = ''
                if distribution_type == 'no_state':
                    remote_execution_type = 'anycast'
                else:
                    remote_execution_type = special_methods[method]['distribution_type'] if method in special_methods else self.distribution_configs['methods'][distribution_type]
                distribution_params = f"req{', ' + method_props['hashkey'] if strategy == 'fragment' and remote_execution_type == 'hashcast' else ''}"
                remote_method_call = f"{'Response res = ' if should_return_value else ''}{remote_execution_type}({distribution_params})"
                null_verification = "if (res.content == \"{}\") return null" if should_return_value else None
                function_return = f"{method_infos['return_type'].replace('[]', '')} response{'[]' if '[]' in method_infos['return_type'] else ''} = {method_props['returnParser'].format('res.content') if 'returnParser' in method_props else 'res.content'}" if should_return_value else None

                methods.append(writer.provide_idented_flow(method_header, [
                    # 'DateTime timeBeforeParamPacking = ic.getTime()',
                    builder.generate_params_packing() if have_params else None,
                    # 'int timeToProcessParamPacking = ls.getMilisecondsExecutionTimeSince(timeBeforeParamPacking)',
                    # 'DateTime timeBeforeParsing = ic.getTime()',
                    "char requestBody[] = je.jsonFromData(params)" if have_params else 'char requestBody[] = ""',
                    # 'int timeToProcessParsing = ls.getMilisecondsExecutionTimeSince(timeBeforeParsing)',
                    # 'DateTime timeBeforeRequestMount = ic.getTime()',
                    f"Request req = new Request(buildMetaForMethod(\"{method}\"), requestBody)",
                    # 'int timeToProcessRequestMount = ls.getMilisecondsExecutionTimeSince(timeBeforeRequestMount)',
                    # 'DateTime timeBeforeMethodCall = ic.getTime()',
                    remote_method_call,
                    # 'int timeToProcessMethodCall = ls.getMilisecondsExecutionTimeSince(timeBeforeMethodCall)',
                    null_verification,
                    # 'DateTime timeBeforeParseReturn = ic.getTime()',
                    function_return,
                    # 'int timeToProcessReturnParsing = ls.getMilisecondsExecutionTimeSince(timeBeforeParseReturn)',
                    # 'logger.storeInfo("{\\"timeToProcessParamPacking\\": \\"$(iu.makeString(timeToProcessParamPacking))\\", \\"timeToProcessParsing\\": \\"$(iu.makeString(timeToProcessParsing))\\", \\"timeToProcessRequestMount\\": \\"$(iu.makeString(timeToProcessRequestMount))\\", \\"timeToProcessMethodCall\\": \\"$(iu.makeString(timeToProcessMethodCall))\\", \\"timeToProcessReturnParsing\\": \\"$(iu.makeString(timeToProcessReturnParsing))\\"}")',
                    "return response" if should_return_value else None
                ]))

        return methods

    def provide_strategy_call_for_order(self, file, order, strategy):
        file.write("{}(req{})\n".format(strategy, order))

class MethodBuilder:
    def __init__(self, name, props, infos):
        self.name = name
        self.props = props
        self.infos = infos

    def generate_params_packing(self) -> str:
        method_name = self.name[0].upper() + self.name[1:]
        parameters = [param.split(' ')[-1].replace("[]", "") for param in (self.infos['parameters'] if 'parameters' in self.infos else [])]
        return f'{method_name}ParamsFormat params = new {method_name}ParamsFormat({", ".join(parameters)})'
    
    def generate_special_packing(self, name) -> str:
        method_name = self.name[0].upper() + self.name[1:]
        return f'{method_name}ParamsFormat params = new {method_name}ParamsFormat({name})'
    
    def get_meta_from(param):
        param_info = param.split(' ')
        if len(param_info) < 3:
            return None, param_info[0], param_info[1].replace('[]', '')
        return param_info[0], param_info[1], param_info[2]

import re
from helpers.extract_helper import extract_method_information_from_interface
from helpers.write_component_helper import WriteComponentHelper
from strategy.configs import strategy_configs

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

    def provide_methods(self, writer: WriteComponentHelper):
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

            pattern = (
                escaped_return_type + ' ' + escaped_interface + ':' + escaped_method + r'\([^)]*\)\s*{\n'
                r'([\s\S]*?)'
                r'\n\s+}'
            )
            method_implementation_code = re.search(pattern, self.component_implementations).group(1)

            # se o método não altera o estado, o proxy deve apenas repassar a chamada da aplicação com base na carga

            method_changes_state = 0

            for attribute in self.attributes:
                assignment_pattern = re.compile(fr"""
                    ^   # Início da linha
                    \s* # Espaço em branco opcional no início
                    
                    # O lado esquerdo da atribuição (variável, atributo, etc.)
                    # Este padrão é simplificado para nomes de variáveis válidos.
                    \b{re.escape(attribute)}\b # Nome de variável válido (ex: 'total', 'soma_global')
                    
                    \s* # Espaço em branco opcional
                    
                    # O operador de atribuição (o ponto principal da regex)
                    (
                        \+= | -= | \*= | /= | %= | \*\*=| //= | &= | \|= | \^= | # Operadores aumentados
                        =(?!=)                 # O '=' simples, desde que não seja seguido por outro '=' (evita '==')
                    )
                    
                    .* # Qualquer coisa após a atribuição até o fim da linha
                """, re.VERBOSE)


                lines_with_state_change = [line for line in method_implementation_code.split('\n') if assignment_pattern.match(line)]
                
                if len(lines_with_state_change) > 0: method_changes_state += 1

            distribution_type = "change" if method_changes_state > 0 else "no_change"
            method_header = f"{method_infos['return_type']} {self.interface_name}:{method}({', '.join(method_infos['parameters'])})"
            have_params = len(method_infos['parameters']) > 0
            should_return_value = method_infos['return_type'] != 'void'

            methods.append(writer.provide_idented_flow(method_header, [
                builder.generate_params_packing() if have_params else None,
                "char requestBody[] = je.jsonFromData(params)" if have_params else 'char requestBody[] = ""',
                f"Request req = new Request(buildMetaForMethod(\"{method}\"), requestBody)",
                f"{'Response res = ' if should_return_value else ''}{self.distribution_configs['methods'][distribution_type]}(req)",
                f"return {method_props['returnParser'].format('res.content') if 'returnParser' in method_props else 'res.content'}" if should_return_value else None,
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

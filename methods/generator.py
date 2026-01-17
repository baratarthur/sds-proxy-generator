import re
from helpers.write_component_helper import WriteComponentHelper
from strategy.configs import strategy_configs

class MethodsGenerator:
    def __init__(self, methods, interface_name, attributes, component_implementations, startegy):
        self.methods = methods
        self.interface_name = interface_name
        self.attributes = attributes
        self.component_implementations = component_implementations
        self.strategy = startegy
        self.distribution_configs = strategy_configs[startegy]

    def provide_method_implementation(self, writer):
        return [
            *self.provide_methods(writer),
            self.provide_metadata_factory(writer)
        ]

    def provide_methods(self, writer: WriteComponentHelper):
        methods = [
            writer.provide_idented_flow('Metadata[] buildMetaForMethod(char method[])', [
                'Metadata metaMethod = new Metadata("method", method)',
                'return new Metadata[](metaMethod)',
            ])
        ]

        for method in self.methods:
            method_props = self.methods[method]
            builder = MethodBuilder(method, method_props, self.interface_name)

            method_params = list(map(builder.argument_map, method_props['parameters']))
            method_header = f"{method_props['returnType']} {self.interface_name}:{method}({', '.join(method_params)})"

            # busca a implementação do componente, deve ser usado quando o método é misto, assim alteramos o método
            escaped_return_type = re.escape(method_props['returnType'])
            escaped_interface = re.escape(self.interface_name)
            escaped_method = re.escape(method)

            # Constrói o padrão regex dinamicamente
            pattern = (
                escaped_return_type + ' ' + escaped_interface + ':' + escaped_method + r'\([^)]*\)\s*{\n'  # Cabeçalho do método
                r'([\s\S]*?)'  # Captura o conteúdo entre as chaves (incluindo novas linhas)
                r'\n    }'  # Fecha a chave do método (indentação de 4 espaços)
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

            methods.append(writer.provide_idented_flow(method_header, [
                builder.generate_params_packing() if len(method_params) > 0 else None,
                "char requestBody[] = je.jsonFromData(params)" if len(method_params) > 0 else 'char requestBody[] = ""',
                f"Request req = new Request(buildMetaForMethod(\"{method}\"), requestBody)",
                f"{'Response res = ' if method_props['returnType'] != 'void' else ''}{self.distribution_configs['methods'][distribution_type]}(req)",
                f"return {method_props['returnParser'].format('res.content') if 'returnParser' in method_props else 'res.content'}" if method_props['returnType'] != 'void' else None,
            ]))

        return methods

    def provide_strategy_call_for_order(self, file, order, strategy):
        file.write("{}(req{})\n".format(strategy, order))

    def provide_metadata_factory(self, writer: WriteComponentHelper):
        return writer.provide_idented_flow("Metadata[] buildMetaForMethod(char method[])", [
            'Metadata metaMethod = new Metadata("method", method)',
            'return new Metadata[](metaMethod)'
        ])

class MethodBuilder:
    def __init__(self, name, props, interface_name):
        self.name = name
        self.props = props
        self.interface_name = interface_name

    def argument_map(self, argument) -> str:
        arg_string = ""
        if 'store' in argument and argument['store']: arg_string += "store "

        if "[]" in argument['type']: arg_string += f"{argument['type'].replace('[]', '')} {argument['name']}[]"
        else: arg_string += f"{argument['type']} {argument['name']}"

        return arg_string

    def generate_params_packing(self) -> str:
        method_name = self.name[0].upper() + self.name[1:]
        parameters = [param['stringParser'].format(param['name']) if 'stringParser' in param else param['name'] for param in (self.props['parameters'] if 'parameters' in self.props else [])]
        return f'{method_name}ParamsFormat params = new {method_name}ParamsFormat({", ".join(parameters)})'

    def build_request(method_name, content=None) -> str:
        if content == None:
            return "new Request(buildMetaForMethod(\"{}\"))\n".format(method_name)
        else:
            return "new Request(buildMetaForMethod(\"{}\"), {})\n".format(method_name, content)


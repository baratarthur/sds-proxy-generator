import re

def extract_component_dependencies(component_text):
    match = re.search(r'requires\s+(.*?)\{', component_text, re.DOTALL)
    
    if match:
        libraries = match.group(1).strip()
        
        component_dependencies = [{ "lib": lib.strip().split(' ')[0], "alias": lib.strip().split(' ')[-1] } for lib in libraries.split(',')]
        return component_dependencies
    
    return []

def filter_unique(dependencies):
    unique_dependencies_libs = list(set(dep['lib'] for dep in dependencies))
    unique_dependencies = []
    for dep in dependencies:
        if dep['lib'] in unique_dependencies_libs:
            unique_dependencies.append(dep)
            unique_dependencies_libs.remove(dep['lib'])
    return unique_dependencies

def extract_method_information_from_interface(interface_file):
    # Regex explicada:
    # ([\w\[\]]+) -> Grupo 1: Tipo de retorno (letras, números ou colchetes para arrays)
    # \s+         -> Um ou mais espaços
    # (\w+)       -> Grupo 2: Nome do método
    # \((.*?)\)   -> Grupo 3: Tudo dentro dos parênteses (parâmetros)
    padrao = r"([\w\[\]]+)\s+(\w+)\s*\((.*?)\)"
    
    matches = re.findall(padrao, interface_file)
    
    extracted_methods = []
    for return_type, name, params in matches:
        params_list = [p.strip() for p in params.split(',')] if params.strip() else []
        
        extracted_methods.append({
            "method": name,
            "return_type": return_type,
            "parameters": params_list
        })
    
    return extracted_methods
   
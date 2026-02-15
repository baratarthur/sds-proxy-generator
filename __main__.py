import os
from config import DidlReader
from helpers.extract_helper import extract_component_dependencies, filter_unique
from helpers.write_component_helper import WriteComponentHelper
from header.generator import HeaderGenerator
from methods.generator import MethodsGenerator
from strategy.configs import strategy_configs
from adaptation.generator import AdaptationGenerator
from remote.generator import RemoteGenerator

IDL_EXTENSION = "didl"

idl_resources = []

for (path, dirname, files) in os.walk("resources"):
    for file in files:
        file_extension_type = file.split(".")[-1]
        if file_extension_type != IDL_EXTENSION: continue
        component_name = file.replace(f".{IDL_EXTENSION}", ".dn")
        target_path = path.replace("resources/", "")
        idl_resources.append({
            "path": path,
            "file": file,
            "target_location": target_path,
            "component_implementation": f"{target_path}/{component_name}",
            "interface_location": f"{path}/{component_name}",
        })

for file_config in idl_resources:
    print(f"Processing {file_config['file']}...")

    didl_filepath = f"{file_config['path']}/{file_config['file']}"
    
    didl_config = None
    component_implementations = ""
    interface_definitions = ""
    
    with open(didl_filepath, "r") as didl_file:
        didl_config = DidlReader(didl_file)

    with open(file_config["component_implementation"], "r") as component_file:
        component_implementations = component_file.read()

    with open(file_config["interface_location"], "r") as interface_file:
        interface_definitions = interface_file.read()

    if not didl_config:
        print(f"Error processing {file_config['file']}: could not read config.")
        continue

    # print(component_implementations)
    # print("================================")
    # print(interface_definitions)

    for strategy in strategy_configs:
        for charachteristic in strategy_configs[strategy]["charachteristics"]:
            proxy_file_name = didl_filepath.split("/")[-1].replace(f".{IDL_EXTENSION}", f".proxy.{strategy}.{charachteristic}.dn")
            output_file_path = f"{file_config['target_location']}/{proxy_file_name}"

            with open(output_file_path, "w") as out_file:
                writer = WriteComponentHelper(out_file)
                dependencies = [*didl_config.dependencies, *strategy_configs[strategy]["dependencies"], *extract_component_dependencies(component_implementations)]
                component_header = HeaderGenerator(file_config["interface_location"], filter_unique(dependencies))
                ComponentMethods = MethodsGenerator(didl_config.methods, component_header.get_interface_name(),
                                                    didl_config.attributes, component_implementations, interface_definitions, strategy)
                ComponentAdaptation = AdaptationGenerator(writer, didl_config.calculate_on_active(strategy, charachteristic),
                                                            didl_config.calculate_on_inactive())

                component = component_header.get_component_flow(writer)
                component(writer, [
                    component_header.provide_addresses(),
                    *component_header.provide_pointer(),
                    "",
                    *ComponentMethods.provide_methods(writer),
                    *[factory(writer) for factory in strategy_configs[strategy]["charachteristics"][charachteristic]],
                    ComponentAdaptation.provide_on_active(),
                    ComponentAdaptation.provide_on_inactive(),
                ])

    component_name = file_config["file"].replace(f".{IDL_EXTENSION}", "")
    component_package = ".".join(file_config['path'].replace("resources/", "").split('/'))
    output_remote_path = f"remotes/Remote.{component_name.lower()}.dn"
    with open(output_remote_path, "w") as out_file:
        remote_generator = RemoteGenerator(file=out_file, component_name=component_name, component_deps=HeaderGenerator.static_provide_component_dependecies(didl_config.dependencies),
                                            component_package=component_package, component_methods=didl_config.methods, interface_definitions=interface_definitions)
        remote_generator.provide_header()
        remote_generator.provide_server_methods()

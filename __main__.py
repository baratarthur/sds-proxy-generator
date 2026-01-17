import os
from config import DidlReader
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
        idl_resources.append(path + "/" + file)

for didl_filepath in idl_resources:
    interface_filepath = didl_filepath.replace(f".{IDL_EXTENSION}", ".dn")

    with open(didl_filepath, "r") as didl_file:
        didl_config = DidlReader(didl_file)
        component_implementations = ""

        with open(didl_config.component_file, "r") as component_file:
            component_implementations = component_file.read()

        # verify if outputpath exists
        if not os.path.exists(didl_config.output_folder):
            os.makedirs(didl_config.output_folder)

        for strategy in strategy_configs:
            for charachteristic in strategy_configs[strategy]["charachteristics"]:
                proxy_file_name = didl_filepath.split("/")[-1].replace(f".{IDL_EXTENSION}", f".proxy.{strategy}.{charachteristic}.dn")
                output_file_path = f"{didl_config.output_folder}/{proxy_file_name}"

                with open(output_file_path, "w") as out_file:
                    writer = WriteComponentHelper(out_file)
                    ComponentHeader = HeaderGenerator(interface_filepath, [*didl_config.dependencies, *strategy_configs[strategy]["dependencies"]])
                    ComponentMethods = MethodsGenerator(didl_config.methods, ComponentHeader.get_interface_name(),
                                                        didl_config.attributes, component_implementations, strategy)
                    ComponentAdaptation = AdaptationGenerator(writer, didl_config.calculate_on_active(strategy, charachteristic),
                                                              didl_config.calculate_on_inactive())

                    component = ComponentHeader.get_component_flow(writer)
                    component(writer, [
                        ComponentHeader.provide_addresses(),
                        *ComponentHeader.provide_pointer(),
                        "",
                        *ComponentMethods.provide_methods(writer),
                        *[factory(writer) for factory in strategy_configs[strategy]["charachteristics"][charachteristic]],
                        ComponentAdaptation.provide_on_active(),
                        ComponentAdaptation.provide_on_inactive(),
                    ])

        component_name = didl_config.component_file.split('/')[-1].replace(".dn", "")
        component_package = ".".join(didl_config.component_file.split('/')[:-1])
        output_remote_path = f"remotes/Remote.{component_name.lower()}.dn"
        with open(output_remote_path, "w") as out_file:
            remote_generator = RemoteGenerator(file=out_file, component_name=component_name, component_deps=HeaderGenerator.static_provide_component_dependecies(didl_config.dependencies),
                                                component_package=component_package, component_methods=didl_config.methods)
            remote_generator.provide_header()
            remote_generator.provide_server_methods()

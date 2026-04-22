from os import path
from shutil import rmtree

import componentize_py
from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version: str, build_data: dict[str, any]) -> None:
        bindings_out_path = path.join(self.directory, "bindings")
        if path.exists(bindings_out_path):
            rmtree(bindings_out_path)

        componentize_py.generate_bindings(
            wit_path=[
                path.join(self.root, "wit", "repo", "pumpkin-plugin-wit", "v0.1")
            ],
            worlds=[],
            features=[],
            all_features=False,
            world_module="wit_world",
            output_dir=bindings_out_path,
            import_interface_names=[],
            export_interface_names=[],
            full_names=False,
        )

        build_data["force_include"][bindings_out_path] = ""

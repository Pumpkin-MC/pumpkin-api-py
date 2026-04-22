import argparse
import os
import tempfile

import componentize_py


def _build_entrypoint_wrapper(app_module: str, wrapper_dir: str) -> str:
    wrapper_name = "_pumpkin_componentize_entry"
    wrapper_path = os.path.join(wrapper_dir, f"{wrapper_name}.py")

    with open(wrapper_path, "w", encoding="utf-8") as wrapper_file:
        wrapper_file.write(
            "from pathlib import Path\n"
            "from pumpkin_api.impl import MetadataImpl, WitWorldImpl\n\n"
            "WitWorld = WitWorldImpl\n"
            "Metadata = MetadataImpl\n\n"
            f"import {app_module}\n"
        )
    return wrapper_name


def main():
    parser = argparse.ArgumentParser(description="Build a Pumpkin Python plugin")
    parser.add_argument(
        "app_module", help="The python module containing the plugin (e.g. 'main')"
    )
    parser.add_argument(
        "-o", "--output", default="plugin.wasm", help="Output wasm file name"
    )
    args = parser.parse_args()

    import pumpkin_api

    pkg_dir = os.path.dirname(pumpkin_api.__file__)
    # In source checkout, they are in wit_files/repo/...
    # In installed package, they are directly in wit_files/
    wit_dir = os.path.join(
        pkg_dir, "..", "..", "wit", "repo", "pumpkin-plugin-wit", "v0.1.0"
    )
    if not os.path.exists(wit_dir):
        wit_dir = os.path.join(pkg_dir, "wit")

    # Pass the parent directory of pumpkin_api to componentize-py so it can resolve `pumpkin_api` module
    # in case it's not installed in a standard site-packages (e.g. editable install or no venv)
    pkg_parent_dir = os.path.dirname(pkg_dir)

    with tempfile.TemporaryDirectory(prefix="pumpkin-api-build-") as wrapper_dir:
        wrapper_module = _build_entrypoint_wrapper(args.app_module, wrapper_dir)

        componentize_py.componentize(
            wit_path=[wit_dir],
            worlds=[],
            features=[],
            all_features=False,
            world_module="wit_world",
            python_path=[".", pkg_parent_dir, wrapper_dir],
            module_worlds=[],
            app_name=wrapper_module,
            output_path=args.output,
            stub_wasi=False,
            import_interface_names=[],
            export_interface_names=[],
            full_names=False,
        )


if __name__ == "__main__":
    main()

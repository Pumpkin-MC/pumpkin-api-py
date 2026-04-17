import argparse
import os
import subprocess
import sys
import tempfile

PUMPKIN_API_VERSION = "0.1.0"
PUMPKIN_API_VERSION_SECTION = "pumpkin:api-version"


def _encode_varuint32(value: int) -> bytes:
    encoded = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            encoded.append(byte | 0x80)
        else:
            encoded.append(byte)
            return bytes(encoded)


def _build_custom_section(name: str, data: bytes) -> bytes:
    name_bytes = name.encode("utf-8")
    payload = _encode_varuint32(len(name_bytes)) + name_bytes + data
    return bytes([0]) + _encode_varuint32(len(payload)) + payload


def _append_api_version_custom_section(output_path: str) -> None:
    with open(output_path, "ab") as wasm_file:
        wasm_file.write(
            _build_custom_section(
                PUMPKIN_API_VERSION_SECTION,
                PUMPKIN_API_VERSION.encode("utf-8"),
            )
        )


def _build_entrypoint_wrapper(app_module: str, wrapper_dir: str) -> str:
    wrapper_name = "_pumpkin_componentize_entry"
    wrapper_path = os.path.join(wrapper_dir, f"{wrapper_name}.py")
    with open(wrapper_path, "w", encoding="utf-8") as wrapper_file:
        wrapper_file.write(
            "from importlib import import_module\n"
            "from pumpkin_api.app import Metadata, WitWorld\n\n"
            f"_user_module = import_module({app_module!r})\n"
            "globals().update(\n"
            "    {\n"
            "        name: getattr(_user_module, name)\n"
            "        for name in dir(_user_module)\n"
            "        if not name.startswith('__')\n"
            "    }\n"
            ")\n"
        )
    return wrapper_name


def main():
    parser = argparse.ArgumentParser(description="Build a Pumpkin Python plugin")
    parser.add_argument("app_module", help="The python module containing the plugin (e.g. 'main')")
    parser.add_argument("-o", "--output", default="plugin.wasm", help="Output wasm file name")
    args = parser.parse_args()

    import pumpkin_api
    pkg_dir = os.path.dirname(pumpkin_api.__file__)
    # In source checkout, they are in wit_files/repo/...
    # In installed package, they are directly in wit_files/
    wit_dir = os.path.join(pkg_dir, "wit_files", "repo", "pumpkin-plugin-wit", "v0.1.0")
    if not os.path.exists(wit_dir):
        wit_dir = os.path.join(pkg_dir, "wit_files")

    # Pass the parent directory of pumpkin_api to componentize-py so it can resolve `pumpkin_api` module
    # in case it's not installed in a standard site-packages (e.g. editable install or no venv)
    pkg_parent_dir = os.path.dirname(pkg_dir)

    with tempfile.TemporaryDirectory(prefix="pumpkin-api-build-") as wrapper_dir:
        wrapper_module = _build_entrypoint_wrapper(args.app_module, wrapper_dir)
        cmd = [
            "componentize-py",
            "-d", wit_dir,
            "-w", "plugin",
            "componentize", wrapper_module,
            "-o", args.output,
            "-p", ".",
            "-p", pkg_parent_dir,
            "-p", wrapper_dir,
        ]

        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd)
        if result.returncode != 0:
            sys.exit(result.returncode)

    _append_api_version_custom_section(args.output)


if __name__ == "__main__":
    main()

# Pumpkin Plugin API for Python

This package provides everything needed to write a Pumpkin server plugin compiled to WebAssembly using Python.

## Quick start

1. Install `pumpkin-api-py`:

```bash
pip install pumpkin-api-py
```

2. Create your plugin (`main.py`):

```python
from pumpkin_api import Plugin, context, logging, metadata, register_plugin

PluginMetadata = metadata.PluginMetadata

class MyPlugin(Plugin):
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="my-python-plugin",
            version="0.1.0",
            authors=["you"],
            description="An example python plugin.",
            dependencies=[],
        )

    def on_load(self, ctx: context.Context) -> None:
        logging.log(logging.Level.INFO, "Python plugin loaded!")

register_plugin(MyPlugin)
```

3. Build your plugin into a WebAssembly component:

```bash
pumpkin-plugin-build main -o my_plugin.wasm
```

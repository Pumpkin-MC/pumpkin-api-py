# Pumpkin Plugin API for Python

This package provides everything needed to write a Pumpkin server plugin compiled to WebAssembly using Python.

## Quick start

1. Install `pumpkin-api-py`:

```bash
pip install pumpkin-api-py
```

2. Create your plugin (`main.py`):

```python
from pumpkin_api import Plugin, PluginMetadata, register_plugin, context, logging

class MyPlugin(Plugin):
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="my-plugin",
            version="0.1.0",
            authors=["you"],
            description="An example python plugin.",
            dependencies=[]
        )

    def on_load(self, ctx: context.Context) -> None:
        logging.log(logging.Level.INFO, "Python plugin loaded!")

register_plugin(MyPlugin)
```

3. Build your plugin into a WebAssembly component:

```bash
pumpkin-api-build main -o my_plugin.wasm
```

For a fuller example with event handling and commands, see [example/main.py](./example/main.py).

from pumpkin_api import (
    Plugin,
    command,
    context,
    event,
    logging,
    metadata,
    permission,
    register_plugin,
    server,
    text,
)

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

        hello_permission = permission.Permission(
            node="my-python-plugin:hello",
            description="Allows using /hello from the Python example plugin.",
            default=permission.PermissionDefault_Allow(),
            children=[],
        )
        ctx.register_permission(hello_permission)

        # Register an event handler
        self.register_event(ctx, event.EventType.PLAYER_JOIN_EVENT, self.on_player_join)

        # Register a command
        cmd = command.Command(["hello"], "A simple hello command")
        self.register_command(ctx, cmd, self.hello_command, "hello")

    def on_player_join(
        self, srv: server.Server, evt: event.PlayerJoinEventData
    ) -> event.PlayerJoinEventData:
        logging.log(logging.Level.INFO, f"Player {evt.player.get_name()} joined!")
        # We can modify the join message
        # evt.join_message = text.TextComponent_text("Welcome to the server!")
        return evt

    def hello_command(
        self,
        sender: command.CommandSender,
        srv: server.Server,
        args: command.ConsumedArgs,
    ) -> int:
        sender.send_message(text.TextComponent.text("Hello from Python!"))
        return 1


register_plugin(MyPlugin)

# pumpkin-api-py: Pumpkin plugin API for Python
# Copyright (C) 2024 alex
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import traceback
from typing import Any, Callable, Dict, Optional, Type

import wit_world
import wit_world.exports
from componentize_py_types import Err
from wit_world.exports import metadata
from wit_world.imports import command, context, event, scheduler, server, text

_PLUGIN_INSTANCE: Optional["Plugin"] = None
_EVENT_HANDLERS: Dict[int, Callable[[server.Server, Any], Any]] = {}
_COMMAND_HANDLERS: Dict[
    int, Callable[[command.CommandSender, server.Server, command.ConsumedArgs], int]
] = {}
_TASK_HANDLERS: Dict[int, Callable[[server.Server], None]] = {}
_NEXT_HANDLER_ID: int = 0


def _exception_message(exc: Exception) -> str:
    if hasattr(exc, "value"):
        value = getattr(exc, "value")
        if value is not None:
            return str(value)
    message = str(exc)
    if message:
        return message
    return "".join(traceback.format_exception_only(type(exc), exc)).strip()


def _format_exception(exc: Exception) -> str:
    details = "".join(
        traceback.format_exception(type(exc), exc, exc.__traceback__)
    ).strip()
    if details:
        return details
    return _exception_message(exc)


def _get_next_handler_id() -> int:
    global _NEXT_HANDLER_ID
    handler_id = _NEXT_HANDLER_ID
    _NEXT_HANDLER_ID += 1
    return handler_id


class Plugin:
    def __init__(self):
        self._pending_events = []

    def metadata(self) -> metadata.PluginMetadata:
        raise NotImplementedError

    def on_load(self, ctx: context.Context) -> None:
        for event_type, handler, priority, blocking in self._pending_events:
            self.register_event(ctx, event_type, handler, priority, blocking)

    def on_unload(self, ctx: context.Context) -> None:
        pass

    def register_event(
        self,
        ctx: context.Context,
        event_type: event.EventType,
        handler: Callable[[server.Server, Any], Any],
        priority=event.EventPriority.NORMAL,
        blocking=True,
    ):
        handler_id = _get_next_handler_id()
        _EVENT_HANDLERS[handler_id] = handler
        ctx.register_event(handler_id, event_type, priority, blocking)

    def register_command(
        self,
        ctx: context.Context,
        cmd: command.Command,
        handler: Callable[
            [command.CommandSender, server.Server, command.ConsumedArgs], int
        ],
        permission: str = "",
    ):
        handler_id = _get_next_handler_id()
        _COMMAND_HANDLERS[handler_id] = handler
        cmd.execute_with_handler_id(handler_id)
        ctx.register_command(cmd, permission)

    def schedule_delayed_task(
        self, delay_ticks: int, handler: Callable[[server.Server], None]
    ) -> int:
        handler_id = _get_next_handler_id()
        _TASK_HANDLERS[handler_id] = handler
        return scheduler.schedule_delayed_task(handler_id, delay_ticks)

    def schedule_repeating_task(
        self,
        delay_ticks: int,
        period_ticks: int,
        handler: Callable[[server.Server], None],
    ) -> int:
        handler_id = _get_next_handler_id()
        _TASK_HANDLERS[handler_id] = handler
        return scheduler.schedule_repeating_task(handler_id, delay_ticks, period_ticks)

    def event_handler(
        self,
        event_type: event.EventType,
        priority=event.EventPriority.NORMAL,
        blocking=True,
    ):
        def decorator(func):
            self._pending_events.append((event_type, func, priority, blocking))
            return func

        return decorator


def register_plugin(plugin_class: Type[Plugin]):
    global _PLUGIN_INSTANCE
    _PLUGIN_INSTANCE = plugin_class()


class WitWorldImpl(wit_world.WitWorld):
    def init_plugin(self) -> None:
        pass

    def on_load(self, context: context.Context) -> None:
        if _PLUGIN_INSTANCE:
            try:
                # In WIT, on-load returns result<_, string>
                # componentize-py handles this by expecting None or raising Err
                _PLUGIN_INSTANCE.on_load(context)
            except Err as e:
                raise Err(_exception_message(e))
            except Exception as e:
                raise Err(_format_exception(e))

    def on_unload(self, context: context.Context) -> None:
        if _PLUGIN_INSTANCE:
            try:
                _PLUGIN_INSTANCE.on_unload(context)
            except Err as e:
                raise Err(_exception_message(e))
            except Exception as e:
                raise Err(_format_exception(e))

    def handle_event(
        self, event_id: int, server: server.Server, event: event.Event
    ) -> event.Event:
        if event_id in _EVENT_HANDLERS:
            # Pass the inner event data to the handler
            result = _EVENT_HANDLERS[event_id](server, event.value)
            # If the handler returns something, assume it's the updated event data
            if result is not None:
                event.value = result
        return event

    def handle_command(
        self,
        command_id: int,
        sender: command.CommandSender,
        server: server.Server,
        args: command.ConsumedArgs,
    ) -> int:
        if command_id in _COMMAND_HANDLERS:
            try:
                return _COMMAND_HANDLERS[command_id](sender, server, args)
            except Exception as e:
                if hasattr(e, "value") and isinstance(
                    e.value,
                    (
                        command.CommandError_InvalidConsumption,
                        command.CommandError_InvalidRequirement,
                        command.CommandError_PermissionDenied,
                        command.CommandError_CommandFailed,
                    ),
                ):
                    raise e
                raise Err(
                    command.CommandError_CommandFailed(
                        text.TextComponent.text(_format_exception(e))
                    )
                )

        raise Err(
            command.CommandError_CommandFailed(
                text.TextComponent.text(
                    f"no handler registered for command id {command_id}"
                )
            )
        )

    def handle_task(self, handler_id: int, server: server.Server) -> None:
        if handler_id in _TASK_HANDLERS:
            _TASK_HANDLERS[handler_id](server)


class MetadataImpl:
    def get_metadata(self) -> metadata.PluginMetadata:
        if _PLUGIN_INSTANCE:
            return _PLUGIN_INSTANCE.metadata()
        return metadata.PluginMetadata("unknown", "0.0.0", [], "No metadata", [])

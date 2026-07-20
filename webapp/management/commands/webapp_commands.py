"""Management commands."""

import textwrap
from typing import Any

from django.core.management import get_commands, load_command_class

from ._base import WebappBaseCommand


class Command(WebappBaseCommand):
    """Management commands."""

    help = "Lists and describes all available management commands."

    def handle(self, *args: Any, **options: Any) -> None:
        super().handle(*args, **options)

        self.banner(["WEBAPP COMMANDS", *textwrap.wrap(self.help)])

        commands = get_commands()

        commands_by_app = {}
        for command, app in commands.items():
            if app == "webapp" or app.startswith("core"):
                if app not in commands_by_app:
                    commands_by_app[app] = []
                commands_by_app[app].append(command)

        for app in commands_by_app.keys():
            self.print(f"{app}")
            for command in commands_by_app[app]:
                if commands[command] == app:
                    self.print(f"  {command}")
                    command_class = load_command_class(app, command)
                    self.print(f"    {command_class.help}")
            self.print("")

        self.check_exit(0)

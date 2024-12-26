import time
from contextlib import contextmanager
from enum import StrEnum
from typing import Any, Generator

from rich import box, get_console
from rich.console import Console, Group
from rich.panel import Panel
from rich.pretty import Pretty
from rich.table import Table
from rich.text import Text

from .constants import Color

console = get_console()


# region ⭐ Printer ⭐


class Printer:

    @staticmethod
    def print_blank() -> None:
        console.print()

    @staticmethod
    def print_banner(title: str, message: str) -> None:
        console.print()
        console.print(
            Panel(
                Text.from_markup(message, justify="center"),
                title=Text(title, style="white on black"),
                width=72,
                style="white on black",
                border_style=Color.BOX_H1.value,
                box=box.ROUNDED,
            )
        )
        console.print()

    @staticmethod
    def print_error(title: str, message: str) -> None:
        console.print()
        console.print(
            Panel(
                Text.from_markup(message, justify="left"),
                title=Text(f"🚨 {title.upper()} 🚨", no_wrap=True, style="white on black"),
                width=72,
                style="white on black",
                border_style=Color.BOX_H1.value,
                box=box.DOUBLE,
            )
        )
        console.print()

    @staticmethod
    def print_box(title: str, message: Any) -> None:
        console.print()
        console.print(
            Panel(
                Pretty(message),
                title=Text(title, style="white on black"),
                style="white on black",
                border_style=Color.BOX_H2.value,
                box=box.ROUNDED,
            )
        )
        console.print()

    @staticmethod
    def print_boxes(title: str, titles_and_messages: list[tuple[str, Any]]) -> None:
        console.print()
        panels = []
        for box_title, box_message in titles_and_messages:
            panels.append(
                Panel(
                    Pretty(box_message),
                    title=Text(box_title, style="white on black"),
                    style="white on black",
                    border_style=Color.BOX_H3.value,
                    box=box.ROUNDED,
                )
            )
        console.print(
            Panel(
                Group(*panels),
                title=title,
                title_align="left",
                style="white on black",
                border_style=Color.BOX_H2.value,
                box=box.ROUNDED,
            )
        )
        console.print()

    @staticmethod
    def print_table(title: str, data: list[tuple[str, str]]) -> None:
        table = Table(show_header=False, box=box.MINIMAL)
        for key, value in data:
            table.add_row(key, value)
        console.print()
        console.print(
            Panel.fit(
                table,
                title=Text(title, style="white on black"),
                style="white on black",
            ),
        )
        console.print()

    @staticmethod
    def simulation_would(message: str | list[str]) -> None:
        if isinstance(message, str):
            message = [message]
        if message:
            message_str = " ↩\n".join(message)
            console.print(f"SIMULATION: Would {message_str}")

    @staticmethod
    def simulation_would_abort(message: str) -> None:
        message = message[:1].lower() + message[1:] if message else ""
        console.print(f"SIMULATION: Would abort because {message}")

    @contextmanager
    def spinner(self) -> Generator[None, None, None]:
        with console.status("", refresh_per_second=10):
            yield

    class Enumerator:
        def __init__(self, console: Console) -> None:
            self.console = console
            self.enumeration = 0
            self.enumeration_start = None

        @property
        def _elapsed_time_str(self) -> str:
            if self.enumeration_start is None:
                return ""
            else:
                elapsed_time = time.perf_counter() - self.enumeration_start
                return f" {elapsed_time:.3f}"

        def do(self, message: str) -> None:
            self.console.print(
                f"#{self.enumeration}{self._elapsed_time_str} {message}",
                highlight=False,
            )
            if self.enumeration_start is None:
                self.enumeration_start = time.perf_counter()

        def done(self) -> None:
            if elapsed_time_str := self._elapsed_time_str:
                self.console.print(f"#{self.enumeration} DONE{elapsed_time_str}s", highlight=False)
            console.print()

            self.enumeration += 1
            self.enumeration_start = None

    @contextmanager
    def enumerator(self) -> Generator[Enumerator, None, None]:
        enumerator = Printer.Enumerator(console)
        try:
            yield enumerator
        finally:
            pass


# endregion ⭐ Printer ⭐


# region ⭐ Markup ⭐


class Markup:
    @staticmethod
    def marks(string: str, marks: str) -> str:
        match marks:
            case "<":
                return f"<{string}>"
            case "[":
                return f"\\[{string}]"
            case "(":
                return f"({string})"
            case "{":
                return f"{{{string}}}"
            case "|":
                return f"|{string}|"
            case "'":
                return f"'{string}'"
            case '"':
                return f'"{string}"'
            case "`":
                return f"`{string}`"
            case "~":
                return f"~{string}~"
            case _:
                return string

    @staticmethod
    def info(text: str, marks: str = "") -> str:
        return Color.TEXT_INFO.markup(Markup.marks(text, marks))

    @staticmethod
    def ok(text: str, marks: str = "") -> str:
        return Color.TEXT_OK.markup(Markup.marks(text, marks))

    @staticmethod
    def not_ok(text: str, marks: str = "") -> str:
        return Color.TEXT_NOT_OK.markup(Markup.marks(text, marks))

    @staticmethod
    def problematic(text: str, marks: str = "") -> str:
        return Color.TEXT_PROBLEMATIC.markup(Markup.marks(text, marks))

    @staticmethod
    def plain(text: str) -> str:
        return Text.from_markup(text).plain

    @staticmethod
    def service(name: str) -> str:
        return Markup.info(name, "<")

    @staticmethod
    def environment(environment: StrEnum) -> str:
        return Markup.info(environment.value, "[")

    @staticmethod
    def mode(mode: StrEnum) -> str:
        return Markup.info(mode.value, "~")


# endregion ⭐ Markup ⭐

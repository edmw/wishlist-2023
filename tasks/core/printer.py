import time
from contextlib import contextmanager
from typing import Generator

from rich import box, get_console
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .constants import Colors

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
                Text(message, justify="center"),
                title=Text(title, style="white on black"),
                width=72,
                style="white on black",
            )
        )
        console.print()

    @staticmethod
    def print_error(title: str, message: str) -> None:
        console.print()
        console.print(
            Panel(
                Text.from_markup(message, justify="left"),
                title=Text(f"🚨 {title} 🚨", no_wrap=True, style="white on black"),
                width=72,
                style="white on black",
                box=box.DOUBLE,
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
                return f"[{string}]"
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
        return Colors.TEXT_INFO.markup(Markup.marks(text, marks))

    @staticmethod
    def ok(text: str, marks: str = "") -> str:
        return Colors.TEXT_OK.markup(Markup.marks(text, marks))

    @staticmethod
    def not_ok(text: str, marks: str = "") -> str:
        return Colors.TEXT_NOT_OK.markup(Markup.marks(text, marks))

    @staticmethod
    def problematic(text: str, marks: str = "") -> str:
        return Colors.TEXT_PROBLEMATIC.markup(Markup.marks(text, marks))

    @staticmethod
    def plain(text: str) -> str:
        return Text.from_markup(text).plain


# endregion ⭐ Markup ⭐

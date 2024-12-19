from contextlib import contextmanager

from rich import box, get_console
from rich.panel import Panel
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text

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

    def __init__(self) -> None:
        self.enumeration = 0

    def print_enumerated(self, message: str, advance: bool = True) -> None:
        if advance:
            self.enumeration += 1
        console.print(f"#{self.enumeration} {message}")

    @contextmanager
    def spinner(self):
        with console.status("", refresh_per_second=10):
            yield


# endregion ⭐ Printer ⭐

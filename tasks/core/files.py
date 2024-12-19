import shutil
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from .printer import Printer

# region ⭐ Files ⭐


class FilesCleaner:
    def __init__(self) -> None:
        self.printer = Printer()
        self.printer.print_banner("🧹🧹🧹", "Cleaning up\nFiles")

    @contextmanager
    def section(self, message: str) -> Generator[None, None, None]:
        self.printer.print_enumerated(message)
        yield
        Printer.print_blank()

    def remove_directory(self, directory: Path, message: str | None = None) -> None:
        if message:
            self.printer.print_enumerated(message, advance=False)
        if directory.exists():
            shutil.rmtree(directory)

    def remove_files_in_directory(self, directory: Path, message: str | None = None) -> None:
        if message:
            self.printer.print_enumerated(message, advance=False)
        for item in directory.iterdir():
            if item.is_file() and item.name != ".gitignore":
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)

    def find_directory_and_remove(self, name: str, directory: Path, message: str | None = None) -> None:
        if message:
            self.printer.print_enumerated(message, advance=False)
        for directory_name in directory.rglob(name):
            shutil.rmtree(directory_name)


# endregion ⭐ Files ⭐

import shutil
from pathlib import Path
from typing import Any, Protocol

from .printer import Markup, Printer

# region ⭐ Files ⭐


class FilesCleanerProtocol(Protocol):

    def remove_directory(self, directory: Path) -> None: ...
    def remove_files_in_directory(self, directory: Path) -> None: ...
    def find_and_remove_in_directory(self, name: str, directory: Path) -> None: ...


class FilesCleanerSimulation(FilesCleanerProtocol):

    def remove_directory(self, directory: Path) -> None:
        Printer.simulation_would(["remove directory", Markup.info(str(directory))])

    def remove_files_in_directory(self, directory: Path) -> None:
        Printer.simulation_would(["remove files in directory", Markup.info(str(directory))])

    def find_and_remove_in_directory(self, name: str, directory: Path) -> None:
        Printer.simulation_would(
            [f"find directory named {Markup.info(name)} and remove in", Markup.info(str(directory))]
        )


class FilesCleaner(FilesCleanerProtocol):

    def __new__(cls, simulation: bool, *args: Any, **kwargs: Any) -> FilesCleanerProtocol:
        if simulation:
            return FilesCleanerSimulation()
        return super(FilesCleaner, cls).__new__(cls)

    def remove_directory(self, directory: Path) -> None:
        if directory.exists():
            shutil.rmtree(directory)

    def remove_files_in_directory(self, directory: Path) -> None:
        for item in directory.iterdir():
            if item.is_file() and item.name != ".gitignore":
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)

    def find_and_remove_in_directory(self, name: str, directory: Path) -> None:
        for directory_name in directory.rglob(name):
            shutil.rmtree(directory_name)


# endregion ⭐ Files ⭐

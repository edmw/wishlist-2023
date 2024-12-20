import shutil
from pathlib import Path

# region ⭐ Files ⭐


class FilesCleaner:

    def remove_directory(self, directory: Path) -> None:
        if directory.exists():
            shutil.rmtree(directory)

    def remove_files_in_directory(self, directory: Path) -> None:
        for item in directory.iterdir():
            if item.is_file() and item.name != ".gitignore":
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)

    def find_directory_and_remove(self, name: str, directory: Path) -> None:
        for directory_name in directory.rglob(name):
            shutil.rmtree(directory_name)


# endregion ⭐ Files ⭐

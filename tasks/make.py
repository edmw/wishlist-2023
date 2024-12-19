from calendar import c
from pdb import run

from invoke.context import Context
from invoke.tasks import task

from .core import FilesCleaner, Paths, Printer


def run_pip(context: Context, arguments: list[str]) -> None:
    context.run(
        " ".join(
            [
                "python -m pip",
                "--require-virtualenv",
                "--quiet",
                *arguments,
            ]
        )
    )


def run_piptools_compile(context: Context, arguments: list[str]) -> None:
    context.run(
        " ".join(
            [
                "python -m piptools",
                "compile",
                "--quiet",
                "--resolver=backtracking",
                "--generate-hashes",
                "--allow-unsafe",
                "--strip-extras",
                *arguments,
            ]
        )
    )


def run_piptools_sync(context: Context, arguments: list[str]) -> None:
    context.run(
        " ".join(
            [
                "python -m piptools",
                "sync",
                "--quiet",
                *arguments,
            ]
        )
    )


@task()
def clean(context: Context) -> None:
    """Cleans up files and directories."""
    cleaner = FilesCleaner()
    with cleaner.section("Removing reports"):
        cleaner.remove_files_in_directory(Paths.REPORTS_COVERAGE_HTML, "Removing coverage reports")
    with cleaner.section("Removing caches"):
        cleaner.remove_directory(Paths.PROJECT / ".cache", "Removing .cache directory")
        cleaner.find_directory_and_remove("__pycache__", Paths.PROJECT, "Removing __pycache__ directories")


@task()
def install_development(context: Context) -> None:
    """Installs development dependencies from requirements file for development into virtual environment."""
    Printer().print_banner("🔧🔧🔧", "Installing\nDevelopment Dependencies")
    printer = Printer()
    printer.print_enumerated("Installing dependencies")
    with printer.spinner():
        run_pip(
            context,
            [
                "install",
                "--upgrade",
                "-r requirements.txt",
                "-r requirements-development.txt",
            ],
        )
    printer.print_enumerated("Checking installed dependencies")
    context.run("python -m pip --require-virtualenv --quiet check")
    Printer.print_blank()


@task()
def install_deployment(context: Context) -> None:
    """Installs deployment dependencies from requirements file into virtual environment."""
    Printer().print_banner("🔧🔧🔧", "Installing\nDeployment Dependencies")
    printer = Printer()
    printer.print_enumerated("Installing dependencies")
    with printer.spinner():
        run_pip(
            context,
            [
                "install",
                "--upgrade",
                "-r requirements.txt",
            ],
        )
    printer.print_enumerated("Checking installed dependencies")
    context.run("python -m pip --require-virtualenv --quiet check")
    Printer.print_blank()


@task()
def sync_development(context: Context) -> None:
    """Syncs development dependencies from requirements file for development into virtual environment."""
    Printer().print_banner("🔧🔧🔧", "Syncing\nDevelopment Dependencies")
    printer = Printer()
    printer.print_enumerated("Syncing dependencies")
    with printer.spinner():
        run_piptools_sync(
            context,
            [
                "requirements.txt",
                "requirements-development.txt",
            ],
        )
    Printer.print_blank()


@task()
def sync_deployment(context: Context) -> None:
    """Syncs deployment dependencies from requirements file into virtual environment."""
    Printer().print_banner("🔧🔧🔧", "Syncing\nDeployment Dependencies")
    printer = Printer()
    printer.print_enumerated("Syncing dependencies")
    with printer.spinner():
        run_piptools_sync(
            context,
            [
                "requirements.txt",
            ],
        )
    Printer.print_blank()


@task()
def pin_development(context: Context) -> None:
    """Pins development dependencies from project file into requirements file for development."""
    Printer().print_banner("🔧🔧🔧", "Pinning\nDevelopment Dependencies")
    printer = Printer()
    printer.print_enumerated("Pinning dependencies")
    with printer.spinner():
        run_piptools_compile(
            context,
            [
                "--extra build",
                "--extra test",
                "--extra check",
                "--extra tool",
                "--extra support",
                "-o requirements-development.txt",
                "pyproject.toml",
            ],
        )
    Printer.print_blank()


@task()
def pin_deployment(context: Context) -> None:
    """Pins deployment dependencies from project file into requirements file."""
    Printer().print_banner("🔧🔧🔧", "Pinning\nDeployment Dependencies")
    printer = Printer()
    printer.print_enumerated("Pinning dependencies")
    with printer.spinner():
        run_piptools_compile(
            context,
            [
                "-o requirements.txt",
                "pyproject.toml",
            ],
        )
    Printer.print_blank()

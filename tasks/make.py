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
                "--strip-extras",
                "--allow-unsafe",
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

    printer = Printer()
    printer.print_banner("🧹🧹🧹", "Cleaning\nProject")
    with printer.enumerator() as enumerator:

        enumerator.do("Removing files")
        enumerator.do("Removing .coverage files")
        cleaner.remove_files_in_directory(Paths.REPORTS_COVERAGE_HTML)
        enumerator.done()

        enumerator.do("Removing caches")
        enumerator.do("Removing .cache directory")
        cleaner.remove_directory(Paths.PROJECT / ".cache")
        enumerator.do("Removing __pycache__ directories")
        cleaner.find_directory_and_remove("__pycache__", Paths.PROJECT)
        enumerator.done()


@task()
def install_development(context: Context) -> None:
    """Installs development dependencies from requirements file for development into virtual environment."""
    printer = Printer()
    printer.print_banner("🔧🔧🔧", "Installing\nDevelopment Dependencies")
    with printer.enumerator() as enumerator:
        enumerator.do("Installing development dependencies")
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
        enumerator.done()

        enumerator.do("Checking installed dependencies")
        context.run("python -m pip --require-virtualenv --quiet check")
        enumerator.done()


@task()
def install_deployment(context: Context) -> None:
    """Installs deployment dependencies from requirements file into virtual environment."""
    printer = Printer()
    printer.print_banner("🔧🔧🔧", "Installing\nDeployment Dependencies")
    with printer.enumerator() as enumerator:
        enumerator.do("Installing deployment dependencies")
        with printer.spinner():
            run_pip(
                context,
                [
                    "install",
                    "--upgrade",
                    "-r requirements.txt",
                ],
            )
        enumerator.done()

        enumerator.do("Checking installed dependencies")
        context.run("python -m pip --require-virtualenv --quiet check")
        enumerator.done()


@task()
def sync_development(context: Context) -> None:
    """Syncs development dependencies from requirements file for development into virtual environment."""
    printer = Printer()
    printer.print_banner("🔧🔧🔧", "Syncing\nDevelopment Dependencies")
    with printer.enumerator() as enumerator:
        enumerator.do("Syncing development dependencies")
        with printer.spinner():
            run_piptools_sync(
                context,
                [
                    "requirements.txt",
                    "requirements-development.txt",
                ],
            )
        enumerator.done()


@task()
def sync_deployment(context: Context) -> None:
    """Syncs deployment dependencies from requirements file into virtual environment."""
    printer = Printer()
    printer.print_banner("🔧🔧🔧", "Syncing\nDeployment Dependencies")
    with printer.enumerator() as enumerator:
        enumerator.do("Syncing deployment dependencies")
        with printer.spinner():
            run_piptools_sync(
                context,
                [
                    "requirements.txt",
                ],
            )
        enumerator.done()


def _pin_or_update_development(
    context: Context, printer: Printer, enumerator: Printer.Enumerator, update: bool
) -> None:
    enumerator.do(f"{'Updating' if update else 'Pinning'} development dependencies")
    with printer.spinner():
        run_piptools_compile(
            context,
            [
                *["--upgrade"] * update,
                "--extra build",
                "--extra test",
                "--extra check",
                "--extra tool",
                "--extra support",
                "-o requirements-development.txt",
                "pyproject.toml",
            ],
        )


def _pin_or_update_deployment(
    context: Context, printer: Printer, enumerator: Printer.Enumerator, update: bool
) -> None:
    enumerator.do(f"{'Updating' if update else 'Pinning'} deployment dependencies")
    with printer.spinner():
        run_piptools_compile(
            context,
            [
                *["--upgrade"] * update,
                "-o requirements.txt",
                "pyproject.toml",
            ],
        )


@task()
def pin_development(context: Context) -> None:
    """Pins development dependencies from project file into requirements file for development."""
    printer = Printer()
    printer.print_banner("🔧🔧🔧", "Pinning\nDevelopment Dependencies")
    with printer.enumerator() as enumerator:
        _pin_or_update_development(context, printer, enumerator, update=False)
        enumerator.done()


@task()
def pin_deployment(context: Context) -> None:
    """Pins deployment dependencies from project file into requirements file."""
    printer = Printer()
    printer.print_banner("🔧🔧🔧", "Pinning\nDeployment Dependencies")
    with printer.enumerator() as enumerator:
        _pin_or_update_deployment(context, printer, enumerator, update=False)
        enumerator.done()


@task()
def pin_dependencies(context: Context) -> None:
    """Pins dependencies from project file into requirements files."""
    printer = Printer()
    printer.print_banner("🔧🔧🔧", "Pinning\nDependencies")
    with printer.enumerator() as enumerator:
        _pin_or_update_development(context, printer, enumerator, update=False)
        enumerator.done()
        _pin_or_update_deployment(context, printer, enumerator, update=False)
        enumerator.done()


@task()
def update_development(context: Context) -> None:
    """Updates development dependencies from project file into requirements file for development."""
    printer = Printer()
    printer.print_banner("🔧🔧🔧", "Updating\nDevelopment Dependencies")
    with printer.enumerator() as enumerator:
        _pin_or_update_development(context, printer, enumerator, update=True)
        enumerator.done()


@task()
def update_deployment(context: Context) -> None:
    """Updates deployment dependencies from project file into requirements file."""
    printer = Printer()
    printer.print_banner("🔧🔧🔧", "Updating\nDeployment Dependencies")
    with printer.enumerator() as enumerator:
        _pin_or_update_deployment(context, printer, enumerator, update=True)
        enumerator.done()


@task()
def update_dependencies(context: Context) -> None:
    """Updates dependencies from project file into requirements files."""
    printer = Printer()
    printer.print_banner("🔧🔧🔧", "Updating\nDependencies")
    with printer.enumerator() as enumerator:
        _pin_or_update_development(context, printer, enumerator, update=True)
        enumerator.done()
        _pin_or_update_deployment(context, printer, enumerator, update=True)
        enumerator.done()

# region Import


from __future__ import annotations

import shutil
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import ModuleType
from typing import Final, Generator, Protocol, cast

import keyring
from invoke.collection import Collection
from invoke.context import Context
from invoke.tasks import Task, task
from rich import box, print
from rich.live import Live
from rich.panel import Panel
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text


def import_module_from_path(module_name: str, module_path: str) -> ModuleType:
    import importlib.util

    absolute_path = Path(module_path).resolve()
    parent_path = absolute_path.parent

    sys.path.insert(0, str(parent_path))

    try:
        spec = importlib.util.spec_from_file_location(module_name, absolute_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            return module
        else:
            raise ImportError(f"Unable to load module: {module_name}")
    finally:
        sys.path.pop(0)
        exc_type, exc_value, _ = sys.exc_info()
        if exc_type is not None:
            raise exc_value


make = import_module_from_path(
    "make",
    "development/make.py",
)
make_build = import_module_from_path(
    "make_build",
    "development/make_build.py",
)


# endregion

# region Setup


PROJECT_NAME = "wishlist"


@dataclass(frozen=True)
class Paths:
    PROJECT: Final[Path] = Path(__file__).resolve().parent
    REPORTS: Final[Path] = PROJECT / "reports"
    REPORTS_COVERAGE: Final[Path] = REPORTS / "coverage"
    REPORTS_COVERAGE_HTML: Final[Path] = REPORTS_COVERAGE / "html"
    ENV_LOCAL: Final[Path] = PROJECT / "environments" / "local"
    ENV_LOCAL_DEPLOY: Final[Path] = PROJECT / "environments" / "local-deploy"
    ENV_TESTING: Final[Path] = PROJECT / "environments" / "testing"
    ENV_COMMON: Final[Path] = PROJECT / "environments" / "common"
    ENV_PRIVATE: Final[Path] = PROJECT / "private" / "environments"
    ENV_PRIVATE_LOCAL: Final[Path] = ENV_PRIVATE / "local"
    ENV_PRIVATE_LOCAL_DEPLOY: Final[Path] = ENV_PRIVATE / "local-deploy"


class Mode(Enum):
    DEVELOP = "develop"
    DEVELOP_DEBUG = "develop_debug"
    DEPLOY = "deploy"


class Bump(Enum):
    PATCH = "patch"
    MINOR = "minor"
    MAJOR = "major"


@dataclass(frozen=True)
class Compose:
    LOCAL: Final[str] = str(Paths.ENV_LOCAL / "docker-compose.yml")
    LOCAL_DEBUG: Final[str] = str(Paths.ENV_LOCAL / "docker-compose.debug.yml")
    LOCAL_DEPLOY: Final[str] = str(Paths.ENV_LOCAL_DEPLOY / "docker-compose.yml")
    COMMON_DATABASE: Final[str] = str(Paths.ENV_COMMON / "docker-compose.database.yml")
    COMMON_DATASTORE: Final[str] = str(Paths.ENV_COMMON / "docker-compose.datastore.yml")
    COMMON_FILES: Final[str] = str(Paths.ENV_COMMON / "docker-compose.files.yml")
    PRIVATE_LOCAL_ENV: Final[str] = str(Paths.ENV_PRIVATE_LOCAL / "docker-compose.env.yml")
    PRIVATE_LOCAL_DEPLOY_ENV: Final[str] = str(Paths.ENV_PRIVATE_LOCAL_DEPLOY / "docker-compose.env.yml")
    TESTING: Final[str] = str(Paths.ENV_TESTING / "docker-compose.yml")


# endregion

# region ⭐ Printer ⭐


class Printer:

    @staticmethod
    def print_banner(title: str, message: str) -> None:
        print()
        print(
            Panel(
                Text(message, justify="center"),
                title=Text(title, style="white on black"),
                width=72,
                style="white on black",
            )
        )
        print()

    def __init__(self) -> None:
        self.enumeration = 0

    def print_enumerated(self, message: str, advance: bool = True) -> None:
        if advance:
            self.enumeration += 1
        print(f"#{self.enumeration} {message}")


# endregion ⭐ Printer ⭐

# region ⭐ Files ⭐


class FilesCleaner:
    def __init__(self) -> None:
        self.printer = Printer()
        self.printer.print_banner("🧹🧹🧹", "Cleaning up\nFiles")

    @contextmanager
    def section(self, message: str) -> Generator[None, None, None]:
        self.printer.print_enumerated(message)
        yield
        print()

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

# region ⭐ Builder ⭐


class BuilderBase:
    def __init__(self, context: Context, platform: str) -> None:
        self.context = context

        self.platform = platform
        self.base_image = make.get_build_base_image()

    def print_build_result(self, build_result: dict[str, str]) -> None:
        print()
        table = Table(box=box.MINIMAL, show_header=False)
        table.add_row("Target", build_result["target"])
        table.add_row("Image name", build_result["image_name"])
        table.add_row("Image size", make.sizeof_fmt(build_result["image_size"]))
        table.add_row("Platform", build_result["platform"])
        table.add_row("Base image", build_result["base_image"])
        print(
            Panel.fit(
                table, title=Text("👷 BUILD RESULT 👷", style="white on black"), style="white on black"
            )
        )
        print()


# region Builder


class Builder(BuilderBase):

    def build(self, mode: Mode = Mode.DEVELOP) -> None:
        match mode:
            case Mode.DEVELOP | Mode.DEVELOP_DEBUG:
                message = "Building Webapp for Development"
            case Mode.DEPLOY:
                message = "Building Webapp for Deployment"
        Printer.print_banner("👷👷👷", message)

        if mode in [Mode.DEVELOP, Mode.DEVELOP_DEBUG]:
            build_result = make_build.build_develop(
                platform=self.platform,
                base_image=self.base_image,
                build_name=PROJECT_NAME,
                output=False,
            )
        elif mode == Mode.DEPLOY:
            build_result = make_build.build_deploy(
                platform=self.platform,
                base_image=self.base_image,
                build_name=PROJECT_NAME,
                output=False,
            )
        else:
            raise ValueError(f"Invalid mode: {mode}")

        self.print_build_result(build_result._asdict())


# endregion Builder

# region ReleaseBuilder


class ReleaseBuilder(BuilderBase):

    def build(self, bump: Bump) -> None:
        message = "Building Webapp for Release"
        Printer.print_banner("👷👷👷", message)

        build_result = make_build.release(
            bump=str(bump),
            platform=self.platform,
            base_image=self.base_image,
            build_name=PROJECT_NAME,
            do_check=True,
        )

        self.print_build_result(build_result._asdict())


# endregion ReleaseBuilder

# endregion ⭐ Builder ⭐

# region ⭐ Runner ⭐


class RunnerProtocol(Protocol):
    context: Context
    options_project: list[str]
    run_manage_options: list[str]

    def banner(self, title: str, message: str) -> None: ...


class RunnerBase:

    def __init__(self, context: Context) -> None:
        self.context = context

        self.options_project = [
            f"--project-name {PROJECT_NAME}",
            '--project-directory "."',
        ]

        self.run_manage_options = [
            *self.options_project,
            f'-f "{Compose.TESTING}"',
            f'-f "{Compose.COMMON_DATABASE}"',
            f'-f "{Compose.COMMON_DATASTORE}"',
        ]

    def banner(self, title: str, message: str) -> None:
        print()
        print(
            Panel(
                Text(message, justify="center"),
                title=Text(title, style="white on black"),
                width=72,
                style="white on black",
            )
        )
        print()

    def build_down_command(self) -> str:
        return " ".join(
            [
                "docker compose",
                *self.run_manage_options,
                "down",
            ]
        )


class RunnerUsesManageCommandProtocol(RunnerProtocol):
    def build_run_manage_command(
        self: RunnerProtocol, command: list[str], python_options: list[str] | None = None
    ) -> str: ...


class RunnerUsesManageCommand(RunnerUsesManageCommandProtocol):

    def build_run_manage_command(self, command: list[str], python_options: list[str] | None = None) -> str:
        return " ".join(
            [
                "docker compose",
                *self.run_manage_options,
                "run",
                "--quiet-pull",
                "--service-ports",
                "--rm",
                "app",
                "python",
                "-Wignore::DeprecationWarning",
                *(python_options if python_options else []),
                "manage.py",
                *command,
            ]
        )

    def run_manage_command(self, command: list[str], python_options: list[str] | None = None) -> None:
        message = f"Running Command\n{command[0]}"
        self.banner("🚀🚀🚀", message)

        self.context.run(
            self.build_run_manage_command(command, python_options=python_options),
            pty=True,
        )


# region Runner


class Runner(RunnerBase):

    def __init__(self, context: Context) -> None:
        super().__init__(context)

        self.options = {
            Mode.DEVELOP: [
                *self.options_project,
                f'-f "{Compose.LOCAL}"',
                f'-f "{Compose.COMMON_DATABASE}"',
                f'-f "{Compose.COMMON_DATASTORE}"',
                f'-f "{Compose.COMMON_FILES}"',
            ],
            Mode.DEVELOP_DEBUG: [
                *self.options_project,
                f'-f "{Compose.LOCAL}"',
                f'-f "{Compose.LOCAL_DEBUG}"',
                f'-f "{Compose.COMMON_DATABASE}"',
                f'-f "{Compose.COMMON_DATASTORE}"',
                f'-f "{Compose.COMMON_FILES}"',
            ],
            Mode.DEPLOY: [
                *self.options_project,
                f'-f "{Compose.LOCAL_DEPLOY}"',
            ],
        }
        if Path(Compose.PRIVATE_LOCAL_ENV).exists():
            self.options[Mode.DEVELOP].append(f'-f "{Compose.PRIVATE_LOCAL_ENV}"')
            self.options[Mode.DEVELOP_DEBUG].append(f'-f "{Compose.PRIVATE_LOCAL_ENV}"')
        if Path(Compose.PRIVATE_LOCAL_DEPLOY_ENV).exists():
            self.options[Mode.DEPLOY].append(f'-f "{Compose.PRIVATE_LOCAL_DEPLOY_ENV}"')

    def get_webapp_key(self, mode: Mode) -> str | None:
        name = "local" if mode in [Mode.DEVELOP, Mode.DEVELOP_DEBUG] else "local-deploy"
        return keyring.get_password("wishlist-webapp_key", name)

    def start(self, mode: Mode = Mode.DEVELOP_DEBUG) -> None:
        match mode:
            case Mode.DEVELOP:
                message = "Running Webapp in Development mode"
            case Mode.DEVELOP_DEBUG:
                message = "Running Webapp in Development mode and debugging enabled"
            case Mode.DEPLOY:
                message = "Running Webapp in Deployment mode"
        self.banner("🚀🚀🚀", message)

        options = self.options[mode]
        command = ["docker compose", *options, "up"]

        webapp_key = self.get_webapp_key(mode)

        self.context.run(
            " ".join(command),
            env={"WEBAPP_KEY": webapp_key},
            pty=True,
        )

    def stop(self, mode: Mode = Mode.DEVELOP_DEBUG) -> None:
        options = self.options[mode]
        command = ["docker compose", *options, "down"]

        self.context.run(
            " ".join(command),
            pty=True,
        )


# endregion Runner

# region TestRunner


class TestRunner(RunnerBase, RunnerUsesManageCommand):

    def start(self, spec: str | None = None, coverage: bool = False, debug: bool = False) -> None:
        command = ["webapp_test"]
        if coverage:
            command.append("--coverage")
        if debug:
            command.append("--debug")
        if spec:
            command.append(f'"{spec}"')
        self.run_manage_command(command, python_options=["-Xfrozen_modules=off"])

    def stop(self) -> None:
        command = self.build_down_command()

        self.context.run(command, pty=True)


# endregion TestRunner

# region CommandRunner


class CommandRunner(RunnerBase, RunnerUsesManageCommand):

    def __init__(self, context: Context, container: str = "app") -> None:
        super().__init__(context)

        self.container = container

    def execute(self, container: str, command: list[str]) -> None:
        message = f"Executing Command\n{command[0]}"
        self.banner("🚀🚀🚀", message)

        self.context.run(
            " ".join(["docker compose", *self.run_manage_options, "exec", container, *command]),
            pty=True,
        )

    def run_manage(self, command: list[str]) -> None:
        self.run_manage_command(command)

    def stop(self) -> None:
        command = self.build_down_command()

        self.context.run(command, pty=True)


# endregion CommandRunner

# endregion ⭐ Runner ⭐

# region ⭐ Tasks ⭐


collection_build = Collection("build")
collection_run = Collection("run")
collection_test = Collection("test")
collection_check = Collection("check")
collection_application = Collection("application")
collection_environment = Collection("environment")

namespace = Collection(
    collection_build,
    collection_run,
    collection_test,
    collection_check,
    collection_application,
    collection_environment,
)

# region build


@task(name="develop")
def build_develop(context: Context) -> None:
    """Builds the webapp for development mode and ARM64 architecture."""
    Builder(context, "linux/arm64").build(mode=Mode.DEVELOP)


@task(name="deploy")
def build_deploy(context: Context) -> None:
    """Builds the webapp for deployment mode and ARM64 architecture."""
    Builder(context, "linux/arm64").build(mode=Mode.DEPLOY)


@task(name="release_patch")
def build_release_patch(context: Context) -> None:
    """Builds the webapp for a patch release and AMD64 architecture."""
    ReleaseBuilder(context, "linux/amd64").build(bump=Bump.PATCH)


@task(name="release_minor")
def build_release_minor(context: Context) -> None:
    """Builds the webapp for a minor release and AMD64 architecture."""
    ReleaseBuilder(context, "linux/amd64").build(bump=Bump.MINOR)


@task(name="release_major")
def build_release_major(context: Context) -> None:
    """Builds the webapp for a major release and AMD64 architecture."""
    ReleaseBuilder(context, "linux/amd64").build(bump=Bump.MAJOR)


# endregion build

# region run


@task(name="develop", pre=[build_develop])
def run_develop(context: Context) -> None:
    """Starts a local server and runs the webapp in development mode."""
    Runner(context).start(mode=Mode.DEVELOP)


@task(name="develop_debug", pre=[build_develop], default=True)
def run(context: Context) -> None:
    """Starts a local server and runs the webapp in development mode with debugging enabled."""
    Runner(context).start()


@task(name="develop_down", pre=[build_develop])
def down_develop(context: Context) -> None:
    """Stops the local server and tears down the webapp from development mode."""
    Runner(context).stop(mode=Mode.DEVELOP)


@task(name="deploy", pre=[build_deploy])
def run_deploy(context: Context) -> None:
    """Starts a local server and runs the webapp in deployment mode."""
    Runner(context).start()


@task(name="deploy_down")
def down_deploy(context: Context) -> None:
    """Stops the local server and tears down the webapp from deployment mode."""
    Runner(context).stop(mode=Mode.DEPLOY)


# endregion run

# region test


@task(name="down", pre=[build_develop])
def test_down(context: Context) -> None:
    """Stops and removes all containers used for testing the webapp."""
    TestRunner(context).stop()


@task(name="run", pre=[build_develop], post=[test_down], default=True, help={"spec": "Run specific test."})
def test(context: Context, spec: str | None = None) -> None:
    """Runs tests for the webapp in development mode."""
    TestRunner(context).start(spec=spec)


@task(name="coverage", pre=[build_develop], post=[test_down], help={"spec": "Run specific test."})
def test_coverage(context: Context, spec: str | None = None) -> None:
    """Runs tests for the webapp in development mode and builds coverage report."""
    TestRunner(context).start(spec=spec, coverage=True)


@task(name="debug", pre=[build_develop], post=[test_down], help={"spec": "Run specific test."})
def test_debug(context: Context, spec: str | None = None) -> None:
    """Runs tests for the webapp in development mode with debugging enabled."""
    TestRunner(context).start(spec=spec, debug=True)


# endregion test

# region check


@task(name="down", pre=[build_develop])
def check_down(context: Context) -> None:
    """Stops and removes all containers used for checking the webapp."""
    CommandRunner(context).stop()


@task(name="run", pre=[build_develop], post=[check_down], default=True)
def check(context: Context) -> None:
    """Runs checks for the webapp in development mode."""
    CommandRunner(context).run_manage(command=["webapp_check"])


# endregion check

# region application


@task(pre=[build_develop])
def translations(context: Context) -> None:
    """"""
    CommandRunner(context).run_manage(command=["webapp_make_translations"])


@task(pre=[build_develop])
def migrations(context: Context) -> None:
    """"""
    CommandRunner(context).run_manage(command=["webapp_make_migrations"])


@task(pre=[build_develop])
def dumpdata(context: Context) -> None:
    """"""
    CommandRunner(context).run_manage(
        command=[
            "dumpdata",
            "core",
            "socialaccount",
            "account",
            "auth",
            "--natural-foreign",
            "--format=yaml",
            '> core_`date +%d-%m-%Y"_"%H_%M_%S`.dump.yaml',
        ]
    )


@task(pre=[build_develop])
def shell(context: Context) -> None:
    """"""
    CommandRunner(context).execute(container="app", command=["bash"])


# endregion application

# region environment


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
    printer = Printer()
    printer.print_banner("🔧🔧🔧", "Installing\nDevelopment Dependencies")
    printer.print_enumerated("Installing dependencies")
    context.run(
        "python -m pip --require-virtualenv --quiet install --upgrade -r requirements.txt -r requirements-development.txt"
    )
    printer.print_enumerated("Checking installed dependencies")
    context.run("python -m pip --require-virtualenv --quiet check")
    print()


@task()
def install_deployment(context: Context) -> None:
    printer = Printer()
    printer.print_banner("🔧🔧🔧", "Installing\nDeployment Dependencies")
    printer.print_enumerated("Installing dependencies")
    context.run(
        "python -m pip --require-virtualenv --quiet install --upgrade -r requirements.txt -r requirements.txt"
    )
    printer.print_enumerated("Checking installed dependencies")
    context.run("python -m pip --require-virtualenv --quiet check")
    print()


@task()
def pin_development(context: Context) -> None:
    printer = Printer()
    printer.print_banner("🔧🔧🔧", "Pinning\nDevelopment Dependencies")
    printer.print_enumerated("Pinning dependencies")
    with Live(Spinner("dots", style="green"), refresh_per_second=10):
        context.run(
            "python -m piptools compile --quiet --resolver=backtracking --generate-hashes --allow-unsafe --strip-extras --extra build --extra test --extra check --extra tool --extra support -o requirements-development.txt pyproject.toml"
        )
    print()


@task()
def pin_deployment(context: Context) -> None:

    printer = Printer()
    printer.print_banner("🔧🔧🔧", "Pinning\nDeployment Dependencies")
    printer.print_enumerated("Pinning dependencies")
    with Live(Spinner("dots", style="green"), refresh_per_second=10):
        context.run(
            "python -m piptools compile --quiet --resolver=backtracking --generate-hashes --allow-unsafe --strip-extras -o requirements.txt pyproject.toml"
        )
    print()


# endregion environment

# endregion ⭐ Tasks ⭐

collection_build.add_task(cast(Task, build_develop))
collection_build.add_task(cast(Task, build_deploy))
collection_build.add_task(cast(Task, build_release_patch))
collection_build.add_task(cast(Task, build_release_minor))
collection_build.add_task(cast(Task, build_release_major))

collection_run.add_task(cast(Task, run_develop))
collection_run.add_task(cast(Task, run))
collection_run.add_task(cast(Task, down_develop))
collection_run.add_task(cast(Task, run_deploy))
collection_run.add_task(cast(Task, down_deploy))

collection_test.add_task(cast(Task, test_down))
collection_test.add_task(cast(Task, test))
collection_test.add_task(cast(Task, test_coverage))
collection_test.add_task(cast(Task, test_debug))

collection_check.add_task(cast(Task, check_down))
collection_check.add_task(cast(Task, check))

collection_application.add_task(cast(Task, translations))
collection_application.add_task(cast(Task, migrations))
collection_application.add_task(cast(Task, dumpdata))
collection_application.add_task(cast(Task, shell))

collection_environment.add_task(cast(Task, clean))
collection_environment.add_task(cast(Task, install_development))
collection_environment.add_task(cast(Task, install_deployment))
collection_environment.add_task(cast(Task, pin_development))
collection_environment.add_task(cast(Task, pin_deployment))

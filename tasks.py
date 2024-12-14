# region Import


from __future__ import annotations

import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import ModuleType
from typing import Final, Protocol

import keyring
from invoke.collection import Collection
from invoke.context import Context
from invoke.tasks import task
from rich import box, print
from rich.panel import Panel
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
    LOCAL: Final[str] = "environments/local/docker-compose.yml"
    LOCAL_DEBUG: Final[str] = "environments/local/docker-compose.debug.yml"
    LOCAL_DEPLOY: Final[str] = "environments/local-deploy/docker-compose.yml"
    COMMON_DATABASE: Final[str] = "environments/common/docker-compose.database.yml"
    COMMON_DATASTORE: Final[str] = "environments/common/docker-compose.datastore.yml"
    COMMON_FILES: Final[str] = "environments/common/docker-compose.files.yml"
    PRIVATE_LOCAL_ENV: Final[str] = "private/environments/local/docker-compose.env.yml"
    PRIVATE_LOCAL_DEPLOY_ENV: Final[str] = "private/environments/local-deploy/docker-compose.env.yml"
    TESTING: Final[str] = "environments/testing/docker-compose.yml"


# endregion

# region Builder


class BuilderBase:
    def __init__(self, context: Context, platform: str):
        self.context = context

        self.platform = platform
        self.base_image = make.get_build_base_image()

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


class Builder(BuilderBase):

    def build(self, mode: Mode = Mode.DEVELOP) -> None:
        match mode:
            case Mode.DEVELOP | Mode.DEVELOP_DEBUG:
                message = "Building Webapp for Development"
            case Mode.DEPLOY:
                message = "Building Webapp for Deployment"
        self.banner("👷👷👷", message)

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


class ReleaseBuilder(BuilderBase):

    def build(self, bump: Bump) -> None:
        message = "Building Webapp for Release"
        self.banner("👷👷👷", message)

        build_result = make_build.release(
            bump=str(bump),
            platform=self.platform,
            base_image=self.base_image,
            build_name=PROJECT_NAME,
            do_check=True,
        )

        self.print_build_result(build_result._asdict())


# endregion Builder

# region Runner


class RunnerProtocol(Protocol):
    context: Context
    options_project: list[str]
    run_manage_options: list[str]

    def banner(self, title: str, message: str) -> None: ...


class RunnerBase:

    def __init__(self, context: Context):
        self.context = context

        self.options_project = [
            f"--project-name {PROJECT_NAME}",
            "--project-directory .",
        ]

        self.run_manage_options = [
            *self.options_project,
            f"-f {Compose.TESTING}",
            f"-f {Compose.COMMON_DATABASE}",
            f"-f {Compose.COMMON_DATASTORE}",
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
        message = f"Executing Command\n{command[0]}"
        self.banner("🚀🚀🚀", message)

        self.context.run(
            self.build_run_manage_command(command, python_options=python_options),
            pty=True,
        )


class Runner(RunnerBase):

    def __init__(self, context: Context):
        super().__init__(context)

        self.options = {
            Mode.DEVELOP: [
                *self.options_project,
                f"-f {Compose.LOCAL}",
                f"-f {Compose.COMMON_DATABASE}",
                f"-f {Compose.COMMON_DATASTORE}",
                f"-f {Compose.COMMON_FILES}",
            ],
            Mode.DEVELOP_DEBUG: [
                *self.options_project,
                f"-f {Compose.LOCAL}",
                f"-f {Compose.LOCAL_DEBUG}",
                f"-f {Compose.COMMON_DATABASE}",
                f"-f {Compose.COMMON_DATASTORE}",
                f"-f {Compose.COMMON_FILES}",
            ],
            Mode.DEPLOY: [
                *self.options_project,
                f"-f {Compose.LOCAL_DEPLOY}",
            ],
        }
        if Path(Compose.PRIVATE_LOCAL_ENV).exists():
            self.options[Mode.DEVELOP].append(f"-f {Compose.PRIVATE_LOCAL_ENV}")
            self.options[Mode.DEVELOP_DEBUG].append(f"-f {Compose.PRIVATE_LOCAL_ENV}")
        if Path(Compose.PRIVATE_LOCAL_DEPLOY_ENV).exists():
            self.options[Mode.DEPLOY].append(f"-f {Compose.PRIVATE_LOCAL_DEPLOY_ENV}")

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


class TestRunner(RunnerBase, RunnerUsesManageCommand):

    def start(self) -> None:
        self.run_manage_command(["webapp_test"], python_options=["-Xfrozen_modules=off"])

    def stop(self) -> None:
        command = self.build_down_command()

        self.context.run(command, pty=True)


class CommandRunner(RunnerBase, RunnerUsesManageCommand):

    def __init__(self, context: Context, container: str = "app"):
        super().__init__(context)

        self.container = container

    def run(self, command: list[str]) -> None:
        self.run_manage_command(command)

    def stop(self) -> None:
        command = self.build_down_command()

        self.context.run(command, pty=True)


# endregion Runner

# region Tasks


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


@task(name="down", pre=[build_develop])
def test_down(context: Context) -> None:
    """Stops and removes all containers used for testing the webapp."""
    TestRunner(context).stop()


@task(name="run", pre=[build_develop], post=[test_down], default=True)
def test(context: Context) -> None:
    """Runs tests for the webapp in development mode."""
    TestRunner(context).start()


@task(name="debug", pre=[build_develop], post=[test_down])
def test_debug(context: Context) -> None:
    """Runs tests for the webapp in development mode with debugging enabled."""
    TestRunner(context).start()


@task(name="down", pre=[build_develop])
def check_down(context: Context) -> None:
    """Stops and removes all containers used for checking the webapp."""
    CommandRunner(context).stop()


@task(name="run", pre=[build_develop], post=[check_down], default=True)
def check(context: Context) -> None:
    """Runs checks for the webapp in development mode."""
    CommandRunner(context).run(command=["webapp_check"])


@task(pre=[build_develop])
def translations(context: Context) -> None:
    """"""
    CommandRunner(context).run(command=["webapp_make_translations"])


@task(pre=[build_develop])
def migrations(context: Context) -> None:
    """"""
    CommandRunner(context).run(command=["webapp_make_migrations"])


@task(pre=[build_develop])
def dumpdata(context: Context) -> None:
    """"""
    CommandRunner(context).run(
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


# endregion

namespace = Collection(
    Collection(
        "build",
        build_develop,
        build_deploy,
        build_release_patch,
        build_release_minor,
        build_release_major,
    ),
    Collection(
        "run",
        run,
        run_develop,
        down_develop,
        run_deploy,
        down_deploy,
    ),
    Collection(
        "test",
        test,
        test_debug,
        test_down,
    ),
    Collection(
        "check",
        check,
        check_down,
    ),
    Collection(
        "webapp",
        migrations,
        translations,
        dumpdata,
    ),
)

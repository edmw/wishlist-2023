from dataclasses import dataclass
from pathlib import Path
from typing import Final, Protocol

import keyring
from invoke.context import Context

from .mode import Mode
from .printer import Printer
from .project import CONFIGURATION


@dataclass(frozen=True)
class Compose:
    LOCAL: Final[str] = str(CONFIGURATION.project_paths.ENV_LOCAL / "docker-compose.yml")
    LOCAL_DEBUG: Final[str] = str(CONFIGURATION.project_paths.ENV_LOCAL / "docker-compose.debug.yml")
    LOCAL_DEPLOY: Final[str] = str(CONFIGURATION.project_paths.ENV_LOCAL_DEPLOY / "docker-compose.yml")
    COMMON_DATABASE: Final[str] = str(
        CONFIGURATION.project_paths.ENV_COMMON / "docker-compose.database.yml"
    )
    COMMON_DATASTORE: Final[str] = str(
        CONFIGURATION.project_paths.ENV_COMMON / "docker-compose.datastore.yml"
    )
    COMMON_FILES: Final[str] = str(CONFIGURATION.project_paths.ENV_COMMON / "docker-compose.files.yml")
    PRIVATE_LOCAL_ENV: Final[str] = str(
        CONFIGURATION.project_paths.ENV_PRIVATE_LOCAL / "docker-compose.env.yml"
    )
    PRIVATE_LOCAL_DEPLOY_ENV: Final[str] = str(
        CONFIGURATION.project_paths.ENV_PRIVATE_LOCAL_DEPLOY / "docker-compose.env.yml"
    )
    TESTING: Final[str] = str(CONFIGURATION.project_paths.ENV_TESTING / "docker-compose.yml")


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
            f"--project-name {CONFIGURATION.project_name}",
            '--project-directory "."',
        ]

        self.run_manage_options = [
            *self.options_project,
            f'-f "{Compose.TESTING}"',
            f'-f "{Compose.COMMON_DATABASE}"',
            f'-f "{Compose.COMMON_DATASTORE}"',
        ]

    def banner(self, title: str, message: str) -> None:
        Printer.print_banner(title, message)

    def build_down_command(self) -> str:
        return " ".join(
            [
                "docker compose",
                *self.run_manage_options,
                "down",
            ]
        )


class RunnerUsesManageCommandProtocol(RunnerProtocol):
    service: str

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
                self.service,
                "python",
                "-Wignore::DeprecationWarning",
                *(python_options if python_options else []),
                "manage.py",
                *command,
            ]
        )

    def run_manage_command(self, command: list[str], python_options: list[str] | None = None) -> None:
        message = f"Running Command on Service {self.service}\n{command[0]}"
        self.banner("🚀🚀🚀", message)

        self.context.run(
            self.build_run_manage_command(command, python_options=python_options),
            pty=True,
        )


class DockerRunner:

    # region Application

    class Application(RunnerBase):

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

    # endregion Application

    # region ApplicationTest

    class ApplicationTest(RunnerBase, RunnerUsesManageCommand):

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

    # endregion ApplicationTest

    # region ApplicationCommand

    class ApplicationCommand(RunnerBase, RunnerUsesManageCommand):

        def __init__(
            self, context: Context, service: str = CONFIGURATION.environment_local.service_app
        ) -> None:
            super().__init__(context)

            self.service = service

        def run_manage(self, command: list[str]) -> None:
            self.run_manage_command(command)

        def stop(self) -> None:
            command = self.build_down_command()

            self.context.run(command, pty=True)

    # endregion ApplicationCommand

    # region ShellCommand

    class ShellCommand(RunnerBase):

        def __init__(self, context: Context, container: str = "app") -> None:
            super().__init__(context)

            self.container = container

        def execute(self, service: str, command: list[str]) -> None:
            message = f"Executing Shell Command on Service <{service}>\n{command[0]}"
            self.banner("🔧🔨🪛", message)

            self.context.run(
                " ".join(["docker compose", *self.run_manage_options, "exec", service, *command]),
                pty=True,
            )

        def stop(self) -> None:
            command = self.build_down_command()

            self.context.run(command, pty=True)

    # endregion ShellCommand


# endregion ⭐ Runner ⭐

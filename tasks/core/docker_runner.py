from dataclasses import dataclass
from pathlib import Path
from typing import Final

import keyring
from invoke.context import Context

from .docker import DockerBase, DockerProtocol
from .mode import Mode
from .printer import Markup
from .project import CONFIGURATION, Environment


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


class RunnerProtocol(DockerProtocol):
    options_project: list[str]
    options_environment: dict[Environment, list[str]]

    def get_webapp_key(self, mode: Mode) -> str | None: ...

    def get_command_options(self, environment: Environment) -> list[str]: ...
    def build_down_command(self, environment: Environment) -> list[str]: ...


class RunnerBase(DockerBase):

    def __init__(self, context: Context, simulation: bool = False) -> None:
        super().__init__(context, simulation)

        self.options_project = [
            f"--project-name {CONFIGURATION.project_name}",
            '--project-directory "."',
        ]

        self.options_environment = {
            Environment.LOCAL: [
                f'-f "{Compose.LOCAL}"',
                f'-f "{Compose.COMMON_DATABASE}"',
                f'-f "{Compose.COMMON_DATASTORE}"',
                f'-f "{Compose.COMMON_FILES}"',
            ],
            Environment.LOCAL_DEPLOY: [
                f'-f "{Compose.LOCAL_DEPLOY}"',
            ],
            Environment.TESTING: [
                f'-f "{Compose.TESTING}"',
                f'-f "{Compose.COMMON_DATABASE}"',
                f'-f "{Compose.COMMON_DATASTORE}"',
            ],
        }
        if Path(Compose.PRIVATE_LOCAL_ENV).exists():
            self.options_environment[Environment.LOCAL].append(f'-f "{Compose.PRIVATE_LOCAL_ENV}"')
        if Path(Compose.PRIVATE_LOCAL_DEPLOY_ENV).exists():
            self.options_environment[Environment.LOCAL_DEPLOY].append(
                f'-f "{Compose.PRIVATE_LOCAL_DEPLOY_ENV}"'
            )

    def get_webapp_key(self, mode: Mode) -> str | None:
        name = "local" if mode in [Mode.DEVELOP, Mode.DEVELOP_DEBUG] else "local-deploy"
        return keyring.get_password("wishlist-webapp_key", name)

    def get_command_options(self, environment: Environment) -> list[str]:
        return self.options_project + self.options_environment[environment]

    def build_down_command(self, environment: Environment) -> list[str]:
        return [
            "docker compose",
            *self.get_command_options(environment),
            "down",
        ]


class RunnerUsesManageCommandProtocol(RunnerProtocol):
    service: str

    def build_run_manage_command(
        self: RunnerProtocol,
        environment: Environment,
        command: list[str],
        python_options: list[str] | None = None,
    ) -> list[str]: ...


class RunnerUsesManageCommand(RunnerUsesManageCommandProtocol):

    def build_run_manage_command(
        self, environment: Environment, command: list[str], python_options: list[str] | None = None
    ) -> list[str]:
        return [
            "docker compose",
            *self.get_command_options(environment),
            "run",
            "--quiet-pull",
            "--service-ports",
            "--rm",
            "--entrypoint=''",
            self.service,
            "python",
            "-Wignore::DeprecationWarning",
            *(python_options if python_options else []),
            "manage.py",
            *command,
        ]

    def run_manage_command(
        self, environment: Environment, command: list[str], python_options: list[str] | None = None
    ) -> None:
        message = (
            f"Running Command {Markup.ok(command[0])} "
            f"on Service {Markup.service(self.service)} "
            f"in Environment {Markup.environment(environment)}"
        )
        self.print_banner("🚀🚀🚀", message)

        self.run_in_context(
            self.build_run_manage_command(environment, command, python_options=python_options),
            env={"WEBAPP_KEY": self.get_webapp_key(Mode.DEVELOP)},
        )


class DockerRunner:

    # region Application

    class Application(RunnerBase):

        def __init__(self, context: Context) -> None:
            super().__init__(context, context.config.get("simulation", False))

            self.mode_options = {
                Mode.DEVELOP: [],
                Mode.DEVELOP_DEBUG: [
                    f'-f "{Compose.LOCAL_DEBUG}"',
                ],
                Mode.PRODUCTION: [],
            }

        def build_command(self, mode: Mode, start: bool) -> list[str]:
            match mode:
                case Mode.DEVELOP:
                    environment = Environment.LOCAL
                case Mode.DEVELOP_DEBUG:
                    environment = Environment.LOCAL
                case Mode.PRODUCTION:
                    environment = Environment.LOCAL_DEPLOY
            return [
                "docker compose",
                *self.get_command_options(environment),
                *self.mode_options[mode],
                "up" if start is True else "down",
            ]

        def start(self, mode: Mode = Mode.DEVELOP_DEBUG) -> None:
            match mode:
                case Mode.DEVELOP:
                    message = "Running Webapp in Development Mode"
                case Mode.DEVELOP_DEBUG:
                    message = "Running Webapp in Development Mode and Debugging Enabled"
                case Mode.PRODUCTION:
                    message = "Running Webapp in Production Mode"
            self.print_banner("🚀🚀🚀", message)

            command = self.build_command(mode, start=True)
            self.run_in_context(command, env={"WEBAPP_KEY": self.get_webapp_key(mode)})

        def stop(self, mode: Mode = Mode.DEVELOP_DEBUG) -> None:
            command = self.build_command(mode, start=False)
            self.run_in_context(command)

    # endregion Application

    # region ApplicationTest

    class ApplicationTest(RunnerBase, RunnerUsesManageCommand):

        def __init__(self, context: Context) -> None:
            super().__init__(context, context.config.get("simulation", False))

            self.service = CONFIGURATION.environments[Environment.LOCAL].service_app

        def start(self, spec: str | None = None, coverage: bool = False, debug: bool = False) -> None:
            command = ["webapp_test"]
            if coverage:
                command.append("--coverage")
            if debug:
                command.append("--debug")
            if spec:
                command.append(f'"{spec}"')
            self.run_manage_command(Environment.TESTING, command, python_options=["-Xfrozen_modules=off"])

        def stop(self) -> None:
            command = self.build_down_command(Environment.TESTING)
            self.run_in_context(command)

    # endregion ApplicationTest

    # region ApplicationCommand

    class ApplicationCommand(RunnerBase, RunnerUsesManageCommand):

        def __init__(
            self,
            context: Context,
            service: str = CONFIGURATION.environments[Environment.LOCAL].service_app,
        ) -> None:
            super().__init__(context, context.config.get("simulation", False))

            self.service = service

        def run_manage(self, command: list[str]) -> None:
            self.run_manage_command(Environment.LOCAL, command)

        def stop(self) -> None:
            command = self.build_down_command(Environment.LOCAL)
            self.run_in_context(command)

    # endregion ApplicationCommand

    # region ShellCommand

    class ShellCommand(RunnerBase):

        def __init__(self, context: Context, container: str = "app", simulation: bool = False) -> None:
            super().__init__(context, context.config.get("simulation", False))

            self.container = container

        def execute(self, service: str, command: list[str]) -> None:
            environment = Environment.LOCAL

            message = (
                f"Executing Command {Markup.ok(command[0])} "
                f"on Service {Markup.service(service)} "
                f"in Environment {Markup.environment(environment)}"
            )
            self.print_banner("🔧🔨🪛", message)

            self.run_in_context(
                [
                    "docker compose",
                    *self.get_command_options(environment),
                    "exec",
                    service,
                    *command,
                ]
            )

        def stop(self) -> None:
            command = self.build_down_command(Environment.LOCAL)
            self.run_in_context(command)

    # endregion ShellCommand


# endregion ⭐ Runner ⭐

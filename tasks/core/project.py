import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

import yaml

from .printer import Markup, Printer

PROJECT_DIRECTORY = Path(__file__).parent.parent.parent


@dataclass(frozen=True)
class _ProjectPaths:
    PROJECT: Final[Path] = PROJECT_DIRECTORY
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


class Environment:

    def _read_docker_compose(self, path: Path) -> dict:
        with open(path / "docker-compose.yml", "r") as file:
            try:
                return yaml.safe_load(file)
            except yaml.YAMLError as e:
                message = f"Error reading docker-compose.yml at {path}: {str(e)}"
                raise ConfigurationError(Markup.plain(message), message) from e

    def _get_docker_compose_value(self, keys: list[str]) -> Any:
        value = self._docker_compose
        for key in keys:
            if key not in value:
                message = (
                    f"Expected key {Markup.ok('.'.join(keys), '')} "
                    f"in {Markup.info('docker-compose.yml')}, "
                    f"but it was not found."
                )
                raise ConfigurationError(Markup.plain(message), message)
            value = value[key]
        return value

    def _get_docker_compose_keys(self, keys: list[str]) -> list[str]:
        value = self._get_docker_compose_value(keys)
        if not isinstance(value, dict):
            message = (
                f"Expected value of type {Markup.not_ok('dict', '<')} "
                f"for key {Markup.ok('.'.join(keys), '')} in "
                f"{Markup.info('docker-compose.yml')}, "
                f"but got {Markup.not_ok(type(value).__name__, '<')}."
            )
            raise ConfigurationError(Markup.plain(message), message)
        return list(value.keys())

    def __init__(self, path: Path) -> None:
        self.path = path

        self._docker_compose = self._read_docker_compose(self.path)

        self.services = self._get_docker_compose_keys(["services"])
        self.service_app = self.try_service("app")
        self.service_database = self.try_service("database")
        self.service_datastore = self.try_service("datastore")

    def try_service(self, service: str) -> str:
        if service in self.services:
            return service
        message = (
            f"Expected service {Markup.ok(service, '')} "
            f"in {Markup.info('docker-compose.yml')}, "
            f"but it was not found."
        )
        raise ConfigurationError(Markup.plain(message), message)


class ConfigurationError(Exception):
    def __init__(self, message: str, rich_message: str):
        super().__init__(message)
        self.rich_message = message


class Configuration:

    def _read_pyproject(self, path: Path) -> dict:
        with open(path / "pyproject.toml") as file:
            try:
                return tomllib.loads(file.read())
            except tomllib.TOMLDecodeError as e:
                message = f"Error reading pyproject.toml at {path}: {str(e)}"
                raise ConfigurationError(Markup.plain(message), message) from e

    def _get_pyproject_value(self, keys: list[str]) -> Any:
        value = self._pyproject
        for key in keys:
            if key not in value:
                message = (
                    f"Expected key {Markup.ok('.'.join(keys), '')} "
                    f"in {Markup.info('pyproject.toml')}, "
                    f"but it was not found."
                )
                raise ConfigurationError(Markup.plain(message), message)
            value = value[key]
        return value

    def _get_pyproject_string(self, keys: list[str]) -> str:
        value = self._get_pyproject_value(keys)
        if not isinstance(value, str):
            message = (
                f"Expected value of type {Markup.not_ok("str", "<")} "
                f"for key {Markup.ok(".".join(keys), "'")} "
                f"in {Markup.info("pyproject.toml")}, "
                f"but got {Markup.not_ok(type(value).__name__, "<")}."
            )
            raise ConfigurationError(Markup.plain(message), message)
        return value

    def __init__(self) -> None:
        self.path = PROJECT_DIRECTORY

        self._pyproject = self._read_pyproject(self.path)

        self.project_paths = _ProjectPaths()
        self.project_name = self._get_pyproject_string(["project", "name"])
        self.base_image_name = self._get_pyproject_string(["deployment", "base_image"])
        self.build_image_name = f"{self.project_name}-webapp"

        self.environment_local = Environment(PROJECT_DIRECTORY / "environments" / "local")


try:
    CONFIGURATION: Final[Configuration] = Configuration()
except ConfigurationError as e:
    Printer.print_error("Unable to Load Project Configuration", str(e))
    sys.exit(1)

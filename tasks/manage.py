from invoke.context import Context

from tasks.core.project import CONFIGURATION, Environment

from .build import build_development
from .core import task
from .core.docker_runner import DockerRunner


@task(pre=[build_development])
def console(context: Context) -> None:
    """"""
    DockerRunner.ApplicationCommand(context).run_manage(command=["shell"])


@task(pre=[build_development])
def translations(context: Context) -> None:
    """"""
    DockerRunner.ApplicationCommand(context).run_manage(command=["webapp_make_translations"])


@task(pre=[build_development])
def migrations(context: Context) -> None:
    """"""
    DockerRunner.ApplicationCommand(context).run_manage(command=["webapp_make_migrations"])


@task(pre=[build_development])
def dumpdata(context: Context) -> None:
    """"""
    DockerRunner.ApplicationCommand(context).run_manage(
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


@task(pre=[build_development])
def shell(
    context: Context, service: str = CONFIGURATION.environments[Environment.LOCAL].service_app
) -> None:
    """Starts a shell in a local service container (default: app) after the server has been started."""
    CONFIGURATION.environments[Environment.LOCAL].try_service(service)
    DockerRunner.ShellCommand(context).execute(service=service, command=["bash"])


@task(pre=[build_development])
def connect_database(context: Context) -> None:
    """Connects to the database console of the local service container after the server has been started."""
    DockerRunner.ShellCommand(context).execute(
        service=CONFIGURATION.environments[Environment.LOCAL].service_database,
        command=["psql", "-U", "postgres"],
    )


@task(pre=[build_development])
def connect_datastore(context: Context) -> None:
    """Connects to the datastore console of the local service container after the server has been
    started."""
    DockerRunner.ShellCommand(context).execute(
        service=CONFIGURATION.environments[Environment.LOCAL].service_datastore, command=["redis-cli"]
    )

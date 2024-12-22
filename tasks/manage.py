from invoke.context import Context
from invoke.tasks import task

from tasks.core.project import CONFIGURATION

from .build import build_develop
from .core.docker_runner import DockerRunner


@task(pre=[build_develop])
def console(context: Context) -> None:
    """"""
    DockerRunner.ApplicationCommand(context).run_manage(command=["shell"])


@task(pre=[build_develop])
def translations(context: Context) -> None:
    """"""
    DockerRunner.ApplicationCommand(context).run_manage(command=["webapp_make_translations"])


@task(pre=[build_develop])
def migrations(context: Context) -> None:
    """"""
    DockerRunner.ApplicationCommand(context).run_manage(command=["webapp_make_migrations"])


@task(pre=[build_develop])
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


@task(pre=[build_develop])
def shell(context: Context, service: str = CONFIGURATION.environment_local.service_app) -> None:
    """Starts a shell in a local container (default: app) after the server has been started."""
    CONFIGURATION.environment_local.try_service(service)
    DockerRunner.ShellCommand(context).execute(service=service, command=["bash"])


@task(pre=[build_develop])
def connect_database(context: Context) -> None:
    """Connects to the console of the local database after the server has been started."""
    DockerRunner.ShellCommand(context).execute(
        service=CONFIGURATION.environment_local.service_database, command=["psql", "-U", "postgres"]
    )


@task(pre=[build_develop])
def connect_datastore(context: Context) -> None:
    """Connects to the console of the local datastore after the server has been started."""
    DockerRunner.ShellCommand(context).execute(
        service=CONFIGURATION.environment_local.service_datastore, command=["redis-cli"]
    )

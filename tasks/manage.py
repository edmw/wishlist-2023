import shlex

from invoke.context import Context

from tasks.core.project import CONFIGURATION, Environment

from .build import build_development
from .core import task
from .core.docker_runner import DockerRunner

# region ⭐ Manage Tasks ⭐


@task(name="run", pre=[build_development], default=True)
def run_command(context: Context, command: str | None = None) -> None:
    """Runs a Django management command in the webapp container.

    If no command is provided, shows the management command list.
    """
    if command is None:
        DockerRunner.ApplicationCommand(context).run_manage(command=["webapp_commands"])
    else:
        DockerRunner.ApplicationCommand(context).run_manage(command=[shlex.quote(command)])


@task(pre=[build_development])
def console(context: Context) -> None:
    """Starts a Python console for the Django webapp."""
    DockerRunner.ApplicationCommand(context).run_manage(command=["shell"], interactive=True)


@task(pre=[build_development])
def translations(context: Context) -> None:
    """Creates or updates translations for the Django webapp."""
    DockerRunner.ApplicationCommand(context).run_manage(command=["webapp_make_translations"])


@task(pre=[build_development])
def migrations(context: Context) -> None:
    """Creates or updates migrations for the Django webapp."""
    DockerRunner.ApplicationCommand(context).run_manage(command=["webapp_make_migrations"])


@task(pre=[build_development])
def migrations_merge(context: Context) -> None:
    """Merges migrations for the Django webapp."""
    DockerRunner.ApplicationCommand(context).run_manage(command=["webapp_make_migrations", "--merge"])


@task(pre=[build_development])
def dumpdata(context: Context) -> None:
    """Dumps the data from the database of the Django webapp to a file."""
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
    DockerRunner.ShellCommand(context).execute(service=service, command=["bash"], interactive=True)


@task(pre=[build_development])
def connect_database(context: Context) -> None:
    """Connects to the database console of the local service container after the server has been started."""
    DockerRunner.ShellCommand(context).execute(
        service=CONFIGURATION.environments[Environment.LOCAL].service_database,
        command=["psql", "-U", "postgres"],
        interactive=True,
    )


@task(pre=[build_development])
def connect_datastore(context: Context) -> None:
    """Connects to the datastore console of the local service container after the server has been started."""  # noqa
    DockerRunner.ShellCommand(context).execute(
        service=CONFIGURATION.environments[Environment.LOCAL].service_datastore,
        command=["redis-cli"],
        interactive=True,
    )


# endregion ⭐ Manage Tasks ⭐

from invoke.context import Context
from invoke.tasks import task

from .build import build_develop
from .core.docker_runner import DockerRunner


@task(name="down", pre=[build_develop])
def check_down(context: Context) -> None:
    """Stops and removes all containers used for checking the webapp."""
    DockerRunner.ApplicationCommand(context).stop()


@task(name="run", pre=[build_develop], post=[check_down], default=True)
def check(context: Context) -> None:
    """Runs checks for the webapp in development mode."""
    DockerRunner.ApplicationCommand(context).run_manage(command=["webapp_check"])

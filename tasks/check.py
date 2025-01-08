from invoke.context import Context

from .build import build_development
from .core import task
from .core.docker_runner import DockerRunner

# region ⭐ Check Tasks ⭐


@task(name="down", pre=[build_development])
def check_down(context: Context) -> None:
    """Stops and removes all containers used for checking the webapp."""
    DockerRunner.ApplicationCommand(context).stop()


@task(name="run", pre=[build_development], post=[check_down], default=True)
def check(context: Context) -> None:
    """Runs checks for the webapp in development mode."""
    DockerRunner.ApplicationCommand(context).run_manage(command=["webapp_check"])


# endregion ⭐ Check Tasks ⭐

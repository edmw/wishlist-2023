from invoke.context import Context
from invoke.tasks import task

from .build import build_develop
from .core import CommandRunner


@task(name="down", pre=[build_develop])
def check_down(context: Context) -> None:
    """Stops and removes all containers used for checking the webapp."""
    CommandRunner(context).stop()


@task(name="run", pre=[build_develop], post=[check_down], default=True)
def check(context: Context) -> None:
    """Runs checks for the webapp in development mode."""
    CommandRunner(context).run_manage(command=["webapp_check"])

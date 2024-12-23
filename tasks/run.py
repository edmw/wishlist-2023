from invoke.context import Context
from invoke.tasks import task

from .build import build_development, build_production
from .core.docker_runner import DockerRunner
from .core.mode import Mode


@task(name="development", pre=[build_development])
def run_development(context: Context) -> None:
    """Starts a local server and runs the webapp in development mode."""
    DockerRunner.Application(context).start(mode=Mode.DEVELOP)


@task(name="development_debug", pre=[build_development], default=True)
def run(context: Context) -> None:
    """Starts a local server and runs the webapp in development mode with debugging enabled."""
    DockerRunner.Application(context).start()


@task(name="development_down", pre=[build_development])
def down_development(context: Context) -> None:
    """Stops the local server and tears down the webapp from development mode."""
    DockerRunner.Application(context).stop(mode=Mode.DEVELOP)


@task(name="production", pre=[build_production])
def run_production(context: Context) -> None:
    """Starts a local server and runs the webapp in production mode."""
    DockerRunner.Application(context).start(mode=Mode.PRODUCTION)


@task(name="production_down", pre=[build_production])
def down_production(context: Context) -> None:
    """Stops the local server and tears down the webapp from production mode."""
    DockerRunner.Application(context).stop(mode=Mode.PRODUCTION)

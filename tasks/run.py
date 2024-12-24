from invoke.context import Context
from invoke.tasks import task

from .build import build_development, build_production
from .core.docker_runner import DockerRunner
from .core.mode import Mode


@task(pre=[build_development])
def _run_development(context: Context) -> None:
    simulation = getattr(context.config, "simulation", False)
    DockerRunner.Application(context, simulation=simulation).start(mode=Mode.DEVELOP)


@task(name="development", post=[_run_development])
def run_development(context: Context, dry: bool = False) -> None:
    """Starts a local server and runs the webapp in development mode."""
    context.config.simulation = dry


@task(pre=[build_development])
def _run(context: Context) -> None:
    simulation = getattr(context.config, "simulation", False)
    DockerRunner.Application(context, simulation=simulation).start()


@task(name="development_debug", post=[_run], default=True)
def run(context: Context, dry: bool = False) -> None:
    """Starts a local server and runs the webapp in development mode with debugging enabled."""
    context.config.simulation = dry


@task(name="development_down", pre=[build_development])
def down_development(context: Context) -> None:
    """Stops the local server and tears down the webapp from development mode."""
    DockerRunner.Application(context).stop(mode=Mode.DEVELOP)


@task(pre=[build_production])
def _run_production(context: Context) -> None:
    simulation = getattr(context.config, "simulation", False)
    DockerRunner.Application(context, simulation=simulation).start(mode=Mode.PRODUCTION)


@task(name="production", post=[_run_production])
def run_production(context: Context, dry: bool = False) -> None:
    """Starts a local server and runs the webapp in production mode."""
    context.config.simulation = dry


@task(name="production_down", pre=[build_production])
def down_production(context: Context) -> None:
    """Stops the local server and tears down the webapp from production mode."""
    DockerRunner.Application(context).stop(mode=Mode.PRODUCTION)

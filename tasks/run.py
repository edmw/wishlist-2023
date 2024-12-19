from invoke.context import Context
from invoke.tasks import task

from .build import build_deploy, build_develop
from .core import DockerRunner, Mode


@task(name="develop", pre=[build_develop])
def run_develop(context: Context) -> None:
    """Starts a local server and runs the webapp in development mode."""
    DockerRunner.Application(context).start(mode=Mode.DEVELOP)


@task(name="develop_debug", pre=[build_develop], default=True)
def run(context: Context) -> None:
    """Starts a local server and runs the webapp in development mode with debugging enabled."""
    DockerRunner.Application(context).start()


@task(name="develop_down", pre=[build_develop])
def down_develop(context: Context) -> None:
    """Stops the local server and tears down the webapp from development mode."""
    DockerRunner.Application(context).stop(mode=Mode.DEVELOP)


@task(name="deploy", pre=[build_deploy])
def run_deploy(context: Context) -> None:
    """Starts a local server and runs the webapp in deployment mode."""
    DockerRunner.Application(context).start(mode=Mode.DEPLOY)


@task(name="deploy_down", pre=[build_deploy])
def down_deploy(context: Context) -> None:
    """Stops the local server and tears down the webapp from deployment mode."""
    DockerRunner.Application(context).stop(mode=Mode.DEPLOY)

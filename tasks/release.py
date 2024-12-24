from invoke.context import Context
from invoke.tasks import task

from .build import build_release_major, build_release_minor, build_release_patch
from .core.docker_pusher import DockerPusher


@task(pre=[build_release_patch])
def _patch(context: Context) -> None:
    simulation = getattr(context.config, "simulation", False)
    DockerPusher.Application(context, simulation).push()


@task(name="patch", post=[_patch])
def patch(context: Context, dry: bool = False) -> None:
    """Creates a webapp release using a new patch version and pushes the image to the registry."""
    context.config.simulation = dry


@task(pre=[build_release_minor])
def _minor(context: Context) -> None:
    simulation = getattr(context.config, "simulation", False)
    DockerPusher.Application(context, simulation).push()


@task(name="minor", post=[_minor])
def minor(context: Context, dry: bool = False) -> None:
    """Creates a webapp release using a new minor version and pushes the image to the registry."""
    context.config.simulation = dry


@task(pre=[build_release_major])
def _major(context: Context) -> None:
    simulation = getattr(context.config, "simulation", False)
    DockerPusher.Application(context, simulation).push()


@task(name="major", post=[_major])
def major(context: Context, dry: bool = False) -> None:
    """Creates a webapp release using a new major version and pushes the image to the registry."""
    context.config.simulation = dry

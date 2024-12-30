from invoke.context import Context

from .build import build_release_major, build_release_minor, build_release_patch
from .core import task
from .core.docker_pusher import DockerPusher

# region ⭐ Release Tasks ⭐


@task(name="patch", pre=[build_release_patch])
def patch(context: Context) -> None:
    """Creates a webapp release using a new patch version and pushes the image to the registry."""
    DockerPusher.Application(context).push()


@task(name="minor", pre=[build_release_minor])
def minor(context: Context) -> None:
    """Creates a webapp release using a new minor version and pushes the image to the registry."""
    DockerPusher.Application(context).push()


@task(name="major", pre=[build_release_major])
def major(context: Context) -> None:
    """Creates a webapp release using a new major version and pushes the image to the registry."""
    DockerPusher.Application(context).push()


# endregion ⭐ Release Tasks ⭐

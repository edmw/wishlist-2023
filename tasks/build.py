from invoke.context import Context
from invoke.tasks import task

from .core.bump import Bump
from .core.docker_builder import DockerBuilder
from .core.mode import Mode


@task(name="develop")
def build_develop(context: Context) -> None:
    """Builds the webapp for development mode and ARM64 architecture."""
    DockerBuilder.Development(context, "linux/arm64").build(mode=Mode.DEVELOP)


@task(name="deploy")
def build_deploy(context: Context) -> None:
    """Builds the webapp for deployment mode and ARM64 architecture."""
    DockerBuilder.Development(context, "linux/arm64").build(mode=Mode.DEPLOY)


@task(name="release_patch")
def build_release_patch(context: Context) -> None:
    """Builds the webapp for a patch release and AMD64 architecture."""
    DockerBuilder.Release(context, "linux/amd64").build(bump=Bump.PATCH)


@task(name="release_minor")
def build_release_minor(context: Context) -> None:
    """Builds the webapp for a minor release and AMD64 architecture."""
    DockerBuilder.Release(context, "linux/amd64").build(bump=Bump.MINOR)


@task(name="release_major")
def build_release_major(context: Context) -> None:
    """Builds the webapp for a major release and AMD64 architecture."""
    DockerBuilder.Release(context, "linux/amd64").build(bump=Bump.MAJOR)

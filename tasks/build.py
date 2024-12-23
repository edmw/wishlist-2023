from invoke.context import Context
from invoke.tasks import task

from .core.bump import Bump
from .core.docker_builder import DockerBuilder
from .core.mode import Mode


@task(name="development")
def build_development(context: Context) -> None:
    """Builds the webapp for development mode and ARM64 architecture."""
    DockerBuilder.Development(context, "linux/arm64").build(mode=Mode.DEVELOP)


@task(name="production")
def build_production(context: Context) -> None:
    """Builds the webapp for production mode and ARM64 architecture."""
    DockerBuilder.Development(context, "linux/arm64").build(mode=Mode.PRODUCTION)


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

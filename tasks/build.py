from contextlib import contextmanager
from typing import Generator

from invoke.context import Context
from invoke.exceptions import Exit
from invoke.tasks import task as invoke_task

from .core import task
from .core.bump import Bump
from .core.docker_builder import DockerBuilder, DockerBuilderError
from .core.mode import Mode
from .core.printer import Printer

EXIT_CODE = 10


# region ⭐ Build Tasks ⭐


@contextmanager
def exit_on_docker_build_errors() -> Generator[None, None, None]:
    try:
        yield
    except DockerBuilderError as e:
        Printer.print_error("Build Error", e.rich_message)
        raise Exit(code=EXIT_CODE) from e


@task(name="development")
def build_development(context: Context) -> None:
    """Builds the webapp image for development mode and ARM64 architecture."""
    with exit_on_docker_build_errors():
        DockerBuilder.Development(context, "linux/arm64").build(mode=Mode.DEVELOP)


@invoke_task(name="production")
def build_production(context: Context, dry: bool = False) -> None:
    """Builds the webapp image for production mode and ARM64 architecture."""
    dry = getattr(context.config, "simulation", dry)
    with exit_on_docker_build_errors():
        DockerBuilder.Development(context, "linux/arm64").build(mode=Mode.PRODUCTION)


@invoke_task(name="release_patch")
def build_release_patch(context: Context, dry: bool = False) -> None:
    """Builds the webapp image for a patch release and AMD64 architecture."""
    dry = getattr(context.config, "simulation", dry)
    with exit_on_docker_build_errors():
        DockerBuilder.Release(context, "linux/amd64").build(bump=Bump.PATCH)


@invoke_task(name="release_minor")
def build_release_minor(context: Context, dry: bool = False) -> None:
    """Builds the webapp image for a minor release and AMD64 architecture."""
    dry = getattr(context.config, "simulation", dry)
    with exit_on_docker_build_errors():
        DockerBuilder.Release(context, "linux/amd64").build(bump=Bump.MINOR)


@invoke_task(name="release_major")
def build_release_major(context: Context, dry: bool = False) -> None:
    """Builds the webapp image for a major release and AMD64 architecture."""
    dry = getattr(context.config, "simulation", dry)
    with exit_on_docker_build_errors():
        DockerBuilder.Release(context, "linux/amd64").build(bump=Bump.MAJOR)


# endregion ⭐ Build Tasks ⭐

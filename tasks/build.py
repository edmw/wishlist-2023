from invoke.context import Context
from invoke.tasks import task

from .core.bump import Bump
from .core.docker_builder import DockerBuilder, DockerBuilderError
from .core.mode import Mode
from .core.printer import Printer


@task(name="development")
def build_development(context: Context, dry: bool = False) -> None:
    """Builds the webapp for development mode and ARM64 architecture."""
    dry = getattr(context.config, "simulation", dry)
    try:
        DockerBuilder.Development(context, "linux/arm64", simulation=dry).build(mode=Mode.DEVELOP)
    except DockerBuilderError as e:
        Printer.print_error("Build Error", e.rich_message)


@task(name="production")
def build_production(context: Context, dry: bool = False) -> None:
    """Builds the webapp for production mode and ARM64 architecture."""
    dry = getattr(context.config, "simulation", dry)
    try:
        DockerBuilder.Development(context, "linux/arm64", simulation=dry).build(mode=Mode.PRODUCTION)
    except DockerBuilderError as e:
        Printer.print_error("Build Error", e.rich_message)


@task(name="release_patch")
def build_release_patch(context: Context, dry: bool = False) -> None:
    """Builds the webapp for a patch release and AMD64 architecture."""
    dry = getattr(context.config, "simulation", dry)
    try:
        DockerBuilder.Release(context, "linux/amd64", simulation=dry).build(bump=Bump.PATCH)
    except DockerBuilderError as e:
        Printer.print_error("Build Error", e.rich_message)


@task(name="release_minor")
def build_release_minor(context: Context, dry: bool = False) -> None:
    """Builds the webapp for a minor release and AMD64 architecture."""
    dry = getattr(context.config, "simulation", dry)
    try:
        DockerBuilder.Release(context, "linux/amd64", simulation=dry).build(bump=Bump.MINOR)
    except DockerBuilderError as e:
        Printer.print_error("Build Error", e.rich_message)


@task(name="release_major")
def build_release_major(context: Context, dry: bool = False) -> None:
    """Builds the webapp for a major release and AMD64 architecture."""
    dry = getattr(context.config, "simulation", dry)
    try:
        DockerBuilder.Release(context, "linux/amd64", simulation=dry).build(bump=Bump.MAJOR)
    except DockerBuilderError as e:
        Printer.print_error("Build Error", e.rich_message)

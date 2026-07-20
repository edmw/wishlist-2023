from invoke.context import Context

from .build import build_development
from .core import task
from .core.docker_runner import DockerRunner

# region ⭐ Test Tasks ⭐


@task(name="down", post=[build_development])
def test_down(context: Context) -> None:
    """Stops and removes all containers used for testing the webapp."""
    DockerRunner.ApplicationTest(context).stop()


@task(
    name="run",
    pre=[build_development],
    post=[test_down],
    default=True,
    help={"spec": "Run specific test."},
)
def test(context: Context, spec: str | None = None) -> None:
    """Runs tests for the webapp in development mode."""
    DockerRunner.ApplicationTest(context).start(spec=spec)


@task(
    name="coverage",
    pre=[build_development],
    post=[test_down],
    help={"spec": "Run specific test."},
)
def test_coverage(context: Context, spec: str | None = None) -> None:
    """Runs tests for the webapp in development mode and builds coverage report."""
    DockerRunner.ApplicationTest(context).start(spec=spec, coverage=True)


@task(
    name="debug",
    pre=[build_development],
    post=[test_down],
    help={"spec": "Run specific test."},
)
def test_debug(context: Context, spec: str | None = None) -> None:
    """Runs tests for the webapp in development mode with debugging enabled."""
    DockerRunner.ApplicationTest(context).start(spec=spec, debug=True)


# endregion ⭐ Test Tasks ⭐

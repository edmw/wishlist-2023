from invoke.context import Context

from .build import build_development
from .core import task
from .core.docker_runner import DockerRunner

# region ⭐ Test Tasks ⭐


def _resolve_spec(context: Context, spec: str | None) -> str | None:
    """Resolve the test spec from flag or CLI remainder.

    Tokens after a standalone ``--`` are not parsed by Invoke but collected in
    ``context.remainder``, so they must be picked up explicitly here. An
    explicit flag value always takes precedence over the remainder.
    """
    if spec is not None:
        return spec
    remainder = context.remainder.strip()
    return remainder or None


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
    DockerRunner.ApplicationTest(context).start(spec=_resolve_spec(context, spec))


@task(
    name="coverage",
    pre=[build_development],
    post=[test_down],
    help={"spec": "Run specific test."},
)
def test_coverage(context: Context, spec: str | None = None) -> None:
    """Runs tests for the webapp in development mode and builds coverage report."""
    DockerRunner.ApplicationTest(context).start(spec=_resolve_spec(context, spec), coverage=True)


@task(
    name="debug",
    pre=[build_development],
    post=[test_down],
    help={"spec": "Run specific test."},
)
def test_debug(context: Context, spec: str | None = None) -> None:
    """Runs tests for the webapp in development mode with debugging enabled."""
    DockerRunner.ApplicationTest(context).start(spec=_resolve_spec(context, spec), debug=True)


# endregion ⭐ Test Tasks ⭐

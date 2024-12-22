from invoke.context import Context
from invoke.tasks import task

from .build import build_develop
from .core.docker_runner import DockerRunner


@task(name="down", pre=[build_develop])
def test_down(context: Context) -> None:
    """Stops and removes all containers used for testing the webapp."""
    DockerRunner.ApplicationTest(context).stop()


@task(name="run", pre=[build_develop], post=[test_down], default=True, help={"spec": "Run specific test."})
def test(context: Context, spec: str | None = None) -> None:
    """Runs tests for the webapp in development mode."""
    DockerRunner.ApplicationTest(context).start(spec=spec)


@task(name="coverage", pre=[build_develop], post=[test_down], help={"spec": "Run specific test."})
def test_coverage(context: Context, spec: str | None = None) -> None:
    """Runs tests for the webapp in development mode and builds coverage report."""
    DockerRunner.ApplicationTest(context).start(spec=spec, coverage=True)


@task(name="debug", pre=[build_develop], post=[test_down], help={"spec": "Run specific test."})
def test_debug(context: Context, spec: str | None = None) -> None:
    """Runs tests for the webapp in development mode with debugging enabled."""
    DockerRunner.ApplicationTest(context).start(spec=spec, debug=True)

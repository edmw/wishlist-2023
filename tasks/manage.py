from invoke.context import Context
from invoke.tasks import task

from .build import build_develop
from .core import DockerRunner


@task(pre=[build_develop])
def translations(context: Context) -> None:
    """"""
    DockerRunner.Command(context).run_manage(command=["webapp_make_translations"])


@task(pre=[build_develop])
def migrations(context: Context) -> None:
    """"""
    DockerRunner.Command(context).run_manage(command=["webapp_make_migrations"])


@task(pre=[build_develop])
def dumpdata(context: Context) -> None:
    """"""
    DockerRunner.Command(context).run_manage(
        command=[
            "dumpdata",
            "core",
            "socialaccount",
            "account",
            "auth",
            "--natural-foreign",
            "--format=yaml",
            '> core_`date +%d-%m-%Y"_"%H_%M_%S`.dump.yaml',
        ]
    )


@task(pre=[build_develop])
def shell(context: Context) -> None:
    """"""
    DockerRunner.Command(context).execute(container="app", command=["bash"])

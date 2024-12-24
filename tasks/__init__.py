from typing import cast

from invoke.collection import Collection
from invoke.context import Context
from invoke.tasks import Task, task
from invoke.util import helpline
from rich import box, inspect
from rich.console import Console
from rich.padding import Padding
from rich.table import Table
from rich.text import Text

from .build import (
    build_development,
    build_production,
    build_release_major,
    build_release_minor,
    build_release_patch,
)
from .check import check, check_down
from .core.project import CONFIGURATION, Environment
from .make import (
    clean,
    install_development,
    install_production,
    pin_dependencies,
    pin_development,
    pin_production,
    sync_development,
    sync_production,
    update_dependencies,
    update_development,
    update_production,
)
from .manage import (
    connect_database,
    connect_datastore,
    console,
    dumpdata,
    migrations,
    shell,
    translations,
)
from .release import major, minor, patch
from .run import down_development, down_production, run, run_development, run_production
from .test import test, test_coverage, test_debug, test_down


def get_tasks(collection: Collection, prefix: str = "") -> list[tuple[str, Task]]:
    tasks = []
    for task_name, task_obj in collection.tasks.items():
        full_task_name = f"{prefix}{task_name}"
        is_default = task_name == collection.default
        if is_default and prefix:
            full_task_name += f" ({prefix[:-1]})"
        tasks.append((full_task_name, task_obj))
    for collection_name, collection_obj in collection.collections.items():
        tasks.extend(get_tasks(collection_obj, prefix=f"{prefix}{collection_name}."))
    return tasks


@task(name="list", default=True)
def list_tasks(context: Context) -> None:
    """Lists all available tasks."""

    # Get all tasks as tuples (task_name, task_obj).
    tasks = get_tasks(collection=namespace)

    # Render the tasks in a table.
    style = "white on black"
    table = Table(box=box.HORIZONTALS, style=style, header_style=style, row_styles=[style])
    table.add_column("Name", justify="left", no_wrap=True)
    table.add_column("Description", justify="left")
    for index, (task_name, task_obj) in enumerate(tasks):
        if task_name.startswith("_"):
            # Skip hidden tasks (names of hidden tasks start with an underscore).
            continue
        else:
            # Render the task name and description. If the next task is in a
            # different section, add a separator. If the task is the default
            # task of a collection, highlight it.
            next_task_name, _ = tasks[index + 1] if index + 1 < len(tasks) else (None, None)
            if next_task_name and task_name.rsplit(".", 1)[0] != next_task_name.rsplit(".", 1)[0]:
                end_section = True
            else:
                end_section = False
            if task_obj.is_default:
                style = "yellow"
            else:
                style = "cyan"
            table.add_row(Text(task_name, style=style), helpline(task_obj), end_section=end_section)

    # Print the table with the tasks.
    console = Console()
    console.print(Padding(table, 1))


@task(name="_configuration")
def show_configuration(context: Context, env: str | None = None) -> None:
    match env:
        case Environment.LOCAL.value:
            inspect(CONFIGURATION.environments[Environment.LOCAL])
        case Environment.LOCAL_DEPLOY.value:
            inspect(CONFIGURATION.environments[Environment.LOCAL_DEPLOY])
        case Environment.TESTING.value:
            inspect(CONFIGURATION.environments[Environment.TESTING])
        case None:
            inspect(CONFIGURATION)


collection_make = Collection("make")
collection_manage = Collection("manage")
collection_build = Collection("build")
collection_release = Collection("release")
collection_check = Collection("check")
collection_test = Collection("test")
collection_run = Collection("run")

namespace = Collection(
    collection_make,
    collection_manage,
    collection_build,
    collection_release,
    collection_check,
    collection_test,
    collection_run,
)
namespace.add_task(cast(Task, list_tasks))
namespace.add_task(cast(Task, show_configuration))

collection_make.add_task(cast(Task, clean))
collection_make.add_task(cast(Task, pin_dependencies))
collection_make.add_task(cast(Task, pin_development))
collection_make.add_task(cast(Task, pin_production))
collection_make.add_task(cast(Task, update_dependencies))
collection_make.add_task(cast(Task, update_development))
collection_make.add_task(cast(Task, update_production))
collection_make.add_task(cast(Task, install_development))
collection_make.add_task(cast(Task, install_production))
collection_make.add_task(cast(Task, sync_development))
collection_make.add_task(cast(Task, sync_production))

collection_manage.add_task(cast(Task, console))
collection_manage.add_task(cast(Task, migrations))
collection_manage.add_task(cast(Task, translations))
collection_manage.add_task(cast(Task, dumpdata))
collection_manage.add_task(cast(Task, shell))
collection_manage.add_task(cast(Task, connect_database))
collection_manage.add_task(cast(Task, connect_datastore))

collection_build.add_task(cast(Task, build_development))
collection_build.add_task(cast(Task, build_production))
collection_build.add_task(cast(Task, build_release_patch))
collection_build.add_task(cast(Task, build_release_minor))
collection_build.add_task(cast(Task, build_release_major))

collection_release.add_task(cast(Task, patch))
collection_release.add_task(cast(Task, minor))
collection_release.add_task(cast(Task, major))

collection_check.add_task(cast(Task, check))
collection_check.add_task(cast(Task, check_down))

collection_test.add_task(cast(Task, test))
collection_test.add_task(cast(Task, test_debug))
collection_test.add_task(cast(Task, test_coverage))
collection_test.add_task(cast(Task, test_down))

collection_run.add_task(cast(Task, run))
collection_run.add_task(cast(Task, run_development))
collection_run.add_task(cast(Task, down_development))
collection_run.add_task(cast(Task, run_production))
collection_run.add_task(cast(Task, down_production))

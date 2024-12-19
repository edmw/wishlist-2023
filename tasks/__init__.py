from typing import cast

from invoke.collection import Collection
from invoke.tasks import Task

from .build import (
    build_deploy,
    build_develop,
    build_release_major,
    build_release_minor,
    build_release_patch,
)
from .check import check, check_down
from .make import (
    clean,
    install_deployment,
    install_development,
    pin_dependencies,
    pin_deployment,
    pin_development,
    sync_deployment,
    sync_development,
    update_dependencies,
    update_deployment,
    update_development,
)
from .manage import dumpdata, migrations, shell, translations
from .run import down_deploy, down_develop, run, run_deploy, run_develop
from .test import test, test_coverage, test_debug, test_down

collection_build = Collection("build")
collection_run = Collection("run")
collection_test = Collection("test")
collection_check = Collection("check")
collection_manage = Collection("manage")
collection_make = Collection("make")

namespace = Collection(
    collection_build,
    collection_run,
    collection_test,
    collection_check,
    collection_manage,
    collection_make,
)

collection_build.add_task(cast(Task, build_develop))
collection_build.add_task(cast(Task, build_deploy))
collection_build.add_task(cast(Task, build_release_patch))
collection_build.add_task(cast(Task, build_release_minor))
collection_build.add_task(cast(Task, build_release_major))

collection_run.add_task(cast(Task, run_develop))
collection_run.add_task(cast(Task, run))
collection_run.add_task(cast(Task, down_develop))
collection_run.add_task(cast(Task, run_deploy))
collection_run.add_task(cast(Task, down_deploy))

collection_test.add_task(cast(Task, test_down))
collection_test.add_task(cast(Task, test))
collection_test.add_task(cast(Task, test_coverage))
collection_test.add_task(cast(Task, test_debug))

collection_check.add_task(cast(Task, check_down))
collection_check.add_task(cast(Task, check))

collection_manage.add_task(cast(Task, translations))
collection_manage.add_task(cast(Task, migrations))
collection_manage.add_task(cast(Task, dumpdata))
collection_manage.add_task(cast(Task, shell))

collection_make.add_task(cast(Task, clean))
collection_make.add_task(cast(Task, pin_development))
collection_make.add_task(cast(Task, pin_deployment))
collection_make.add_task(cast(Task, pin_dependencies))
collection_make.add_task(cast(Task, update_development))
collection_make.add_task(cast(Task, update_deployment))
collection_make.add_task(cast(Task, update_dependencies))
collection_make.add_task(cast(Task, install_development))
collection_make.add_task(cast(Task, install_deployment))
collection_make.add_task(cast(Task, sync_development))
collection_make.add_task(cast(Task, sync_deployment))

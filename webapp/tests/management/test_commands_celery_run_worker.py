from webapp.management.commands.celery_run_worker import Command


def test_import() -> None:
    assert Command

from webapp.management.commands.celery_run_beat import Command


def test_import() -> None:
    assert Command

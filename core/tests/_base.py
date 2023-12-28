import logging

import pytest


class AssertLoggingMixin:
    def assert_log(
        self,
        caplog: pytest.LogCaptureFixture,
        level: int,
        message: str,
        clear: bool = True,
    ) -> None:
        record = caplog.records[0]
        assert record.levelno == level
        assert message in record.message
        if clear:
            caplog.clear()

    def assert_log_critical(
        self,
        caplog: pytest.LogCaptureFixture,
        message: str,
        clear: bool = True,
    ) -> None:
        self.assert_log(caplog, logging.CRITICAL, message, clear=clear)

    def assert_log_permission_denied_other_user(
        self,
        caplog: pytest.LogCaptureFixture,
        clear: bool = True,
    ) -> None:
        self.assert_log_critical(
            caplog, "PermissionDenied: Authenticated user requesting other user’s data.", clear=clear
        )

    def assert_log_permission_denied_other_list(
        self,
        caplog: pytest.LogCaptureFixture,
        clear: bool = True,
    ) -> None:
        self.assert_log_critical(
            caplog, "PermissionDenied: Authenticated user requesting other user’s lists.", clear=clear
        )

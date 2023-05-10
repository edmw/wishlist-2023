"""Tests made by the Core Health application."""

from http import HTTPStatus

import pytest
from rest_framework.response import Response

from core_health import HealthCheckResult, HealthCheckResults
from core_health.views.healthcheck import ChecksJSONRenderer, ChecksTextRenderer

COMPONENT_1 = "Test-Component-1"
COMPONENT_2 = "Test-Component-2"
CHECK_1 = "Check#1"
CHECK_2 = "Check#2"


def test_adding_healthchecks() -> None:
    """Asserts checks will get converted and can be added to a collection
    of health checks.
    """
    results = HealthCheckResults()
    assert isinstance(results, list)
    assert len(results) == 0
    results += [(True, COMPONENT_1, 1, CHECK_1)]
    assert len(results) == 1
    results = results + [(True, COMPONENT_1, 1, CHECK_2)]
    assert len(results) == 2
    results += [(True, COMPONENT_2, 1, CHECK_1)]
    assert len(results) == 3
    results = results + [(True, COMPONENT_2, 1, CHECK_2)]
    assert len(results) == 4
    assert all(isinstance(r, HealthCheckResult) for r in results)


@pytest.fixture()
def report() -> list[HealthCheckResult]:
    """Defines test check results."""
    return [
        HealthCheckResult(True, COMPONENT_1, 1, CHECK_1),
        HealthCheckResult(False, COMPONENT_1, 1, CHECK_2),
    ]


@pytest.fixture()
def render_context() -> dict:
    """Defines render context for testing renderers."""
    return {"response": Response(status=HTTPStatus.OK)}


def test_report_formatting_plain_text(report: list[HealthCheckResult], render_context: dict) -> None:
    """Asserts text renderer produces valid and complete output."""
    content = ChecksTextRenderer().render(
        report,
        renderer_context=render_context,
    )
    assert (
        content
        == """True   [Test-Component-1][0001] Check#1
False  [Test-Component-1][0001] Check#2
"""
    )


def test_report_formatting_json_binary(report: list[HealthCheckResult], render_context: dict) -> None:
    """Asserts JSON renderer produces valid and complete output."""
    content = ChecksJSONRenderer().render(
        report,
        renderer_context=render_context,
    )
    assert (
        content
        == b'[{"status":true,"component_name":"Test-Component-1","check_id":1,"check_text":"Check#1"},'
        b'{"status":false,"component_name":"Test-Component-1","check_id":1,"check_text":"Check#2"}]'
    )

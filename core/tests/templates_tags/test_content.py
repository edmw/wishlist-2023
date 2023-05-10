import pytest
from django.test.client import RequestFactory

from core.templates_tags.content import link_to_previous, progress_meter


def test_link_to_previous() -> None:
    request = RequestFactory().get("/?p=/link/to/anywhere")
    assert link_to_previous({"request": request}, "link").startswith('<a href="/link/to/anywhere" ')


def test_link_to_previous_no_request() -> None:
    assert link_to_previous({}, "link") == ""


def test_link_to_previous_no_p() -> None:
    request = RequestFactory().get("/")
    assert link_to_previous({"request": request}, "link") == ""


def test_link_to_previous_invalid_p() -> None:
    request1 = RequestFactory().get("/?p=http://example.com")
    assert link_to_previous({"request": request1}, "link") == ""
    request2 = RequestFactory().get("/?p=//example.com")
    assert link_to_previous({"request": request2}, "link") == ""


def test_progress_meter() -> None:
    assert progress_meter(5, 25) == '<small class="text-muted">(5/25)</small>'
    assert progress_meter(25, 5) == '<small class="text-muted">(25/5)</small>'


def test_progress_meter_raises_on_string_input() -> None:
    with pytest.raises(ValueError, match="Unknown format code"):
        progress_meter(25, "b")
    with pytest.raises(ValueError, match="Unknown format code"):
        progress_meter("a", 25)
    with pytest.raises(ValueError, match="Unknown format code"):
        progress_meter("a", "b")

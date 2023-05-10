from core.services import URLService


def test_url_is_absolute_path() -> None:
    assert URLService.url_is_absolute_path(url="/")
    assert URLService.url_is_absolute_path(url="/path/to/anywhere")
    assert not URLService.url_is_absolute_path(url="")
    assert not URLService.url_is_absolute_path(url="http://example.com")
    assert not URLService.url_is_absolute_path(url="//example.com")
    assert not URLService.url_is_absolute_path(url="example.com")


def test_update_query_parameters() -> None:
    assert URLService.update_query_parameters(url="", parameters={}) == ""
    assert URLService.update_query_parameters(url="/", parameters={}) == "/"
    assert URLService.update_query_parameters(url="/", parameters={"a": ["1"]}) == "/?a=1"
    assert URLService.update_query_parameters(url="/?b=2", parameters={}) == "/?b=2"
    assert URLService.update_query_parameters(url="/?c=3", parameters={"d": ["4"]}) == "/?c=3&d=4"
    assert URLService.update_query_parameters(url="/?e=5", parameters={"e": ["6"]}) == "/?e=6"
    assert (
        URLService.update_query_parameters(
            url="http://user:pass@example.com/path;param/file?q=query", parameters={"any": ["thing"]}
        )
        == "http://user:pass@example.com/path;param/file?q=query&any=thing"
    )

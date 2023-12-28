"""The Core’s template tags for rendering content."""

from datetime import datetime
from typing import Any

from django import template
from django.template import defaulttags
from django.templatetags.static import static
from django.utils.encoding import escape_uri_path
from django.utils.html import escape
from django.utils.safestring import SafeText, mark_safe
from django.utils.translation import gettext as _

from core.services import FormattingService, RenderService, URLService
from webapp.services import LanguageService

register = template.Library()


#  ######## ######## ##     ## ########
#     ##    ##        ##   ##     ##
#     ##    ##         ## ##      ##
#     ##    ######      ###       ##
#     ##    ##         ## ##      ##
#     ##    ##        ##   ##     ##
#     ##    ######## ##     ##    ##


def span(text: str, classes: list[SafeText]) -> SafeText:
    """Renders text."""
    # SECURITY: `classes` is safe.
    # SECURITY: `text` is escaped.
    return mark_safe(f'<span class="{" ".join(classes)}">{escape(_(text))}</span>')  # nosec


@register.simple_tag
def cheering(text: str) -> SafeText:
    """Renders success text."""
    # SECURITY: Literal is safe.
    return span(text, [mark_safe("text-success")])  # nosec


@register.simple_tag
def booing(text: str) -> SafeText:
    """Renders failure text."""
    # SECURITY: Literal is safe.
    return span(text, [mark_safe("text-danger")])  # nosec


@register.simple_tag
def informative(text: str) -> SafeText:
    """Renders informational text."""
    # SECURITY: Literal is safe
    return span(text, [mark_safe("text-secondary")])  # nosec


@register.simple_tag
def progress_meter(current: int, total: int) -> SafeText:
    """Renders a progress meter."""
    # SECURITY: `current` is of type integer.
    # SECURITY: `total` is of type integer.
    return mark_safe(f'<small class="text-muted">({current:d}/{total:d})</small>')  # nosec


#  ##     ##    ###    ########  ##    ## ########   #######  ##      ## ##    ##
#  ###   ###   ## ##   ##     ## ##   ##  ##     ## ##     ## ##  ##  ## ###   ##
#  #### ####  ##   ##  ##     ## ##  ##   ##     ## ##     ## ##  ##  ## ####  ##
#  ## ### ## ##     ## ########  #####    ##     ## ##     ## ##  ##  ## ## ## ##
#  ##     ## ######### ##   ##   ##  ##   ##     ## ##     ## ##  ##  ## ##  ####
#  ##     ## ##     ## ##    ##  ##   ##  ##     ## ##     ## ##  ##  ## ##   ###
#  ##     ## ##     ## ##     ## ##    ## ########   #######   ###  ###  ##    ##


@register.simple_tag(takes_context=True)
def render_markdown(context: template.Context, value: str) -> SafeText:
    if value in (None, ""):
        # SECURITY: Empty string is safe.
        return mark_safe("")  # nosec

    # This is a sanity check while developing which can be safely removed in production.
    assert isinstance(value, str)  # nosec

    return RenderService.render_markdown(value=value)


@register.simple_tag(takes_context=True)
def render_markdown_to_text(context: template.Context, value: str) -> SafeText:
    if value in (None, ""):
        # SECURITY: Empty string is safe.
        return mark_safe("")  # nosec

    # This is a sanity check while developing which can be safely removed in production.
    assert isinstance(value, str)  # nosec

    return RenderService.render_markdown_to_text(value=value)


#  ########     ###    ######## ######## ######## #### ##     ## ########
#  ##     ##   ## ##      ##    ##          ##     ##  ###   ### ##
#  ##     ##  ##   ##     ##    ##          ##     ##  #### #### ##
#  ##     ## ##     ##    ##    ######      ##     ##  ## ### ## ######
#  ##     ## #########    ##    ##          ##     ##  ##     ## ##
#  ##     ## ##     ##    ##    ##          ##     ##  ##     ## ##
#  ########  ##     ##    ##    ########    ##    #### ##     ## ########


@register.simple_tag(takes_context=True)
def render_datetime(context: template.Context, value: datetime, *args: Any, **kwargs: Any) -> SafeText:
    if value in (None, ""):
        # SECURITY: Empty string is safe.
        return mark_safe("")  # nosec

    # This is a sanity check while developing which can be safely removed in production.
    assert isinstance(value, datetime)  # nosec

    return RenderService.render_datetime(value=value)


@register.filter(expects_localtime=True)
def datetime_format(value: datetime, arg: str | None = None) -> str:
    if value in (None, ""):
        return ""

    # This is a sanity check while developing which can be safely removed in production.
    assert isinstance(value, datetime)  # nosec

    language_code = LanguageService.get_language_code()
    return FormattingService.format_datetime(value=value, language_code=language_code)


@register.filter(expects_localtime=True)
def datetime_natural(value: datetime, arg: str | None = None) -> str:
    if value in (None, ""):
        return ""

    # This is a sanity check while developing which can be safely removed in production.
    assert isinstance(value, datetime)  # nosec

    language_code = LanguageService.get_language_code()
    return FormattingService.natural_datetime(value=value, language_code=language_code)


#  ####  ######   #######  ##    ##  ######
#   ##  ##    ## ##     ## ###   ## ##    ##
#   ##  ##       ##     ## ####  ## ##
#   ##  ##       ##     ## ## ## ##  ######
#   ##  ##       ##     ## ##  ####       ##
#   ##  ##    ## ##     ## ##   ### ##    ##
#  ####  ######   #######  ##    ##  ######


@register.simple_tag
def icon(name: str) -> SafeText:
    feather = static("core/icons/feather.svg")
    # SECURITY: `feather` is safe.
    # SECURITY: `name` is escaped.
    return mark_safe(  # nosec
        f'<svg class="feather"><use xlink:href="{feather}#{escape(name)}"></use></svg>'
    )


@register.simple_tag
def icon_large(name: str) -> SafeText:
    feather = static("core/icons/feather.svg")
    # SECURITY: `feather` is safe.
    # SECURITY: `name` is escaped.
    return mark_safe(  # nosec
        f'<svg class="feather-large"><use xlink:href="{feather}#{escape(name)}"></use></svg>'
    )


#  ##       #### ##    ## ##    ##  ######
#  ##        ##  ###   ## ##   ##  ##    ##
#  ##        ##  ####  ## ##  ##   ##
#  ##        ##  ## ## ## #####     ######
#  ##        ##  ##  #### ##  ##         ##
#  ##        ##  ##   ### ##   ##  ##    ##
#  ######## #### ##    ## ##    ##  ######


class LinkToURLNode(template.Node):
    def __init__(self, urlnode: defaulttags.URLNode):
        self.urlnode = urlnode

    def __repr__(self) -> str:
        return f"<{self.__class__.__qualname__} url_node='{repr(self.urlnode)}'>"

    def render(self, context: template.Context) -> str:
        url = self.urlnode.render(context)
        if request := context.get("request"):
            url = URLService.update_query_parameters(
                url=url,
                parameters={"p": [request.path]},
            )
        return url


@register.tag
def linked_url(parser: template.base.Parser, token: template.base.Token) -> LinkToURLNode:
    urlnode = defaulttags.url(parser, token)
    return LinkToURLNode(urlnode)


@register.simple_tag(takes_context=True)
def make_linked_url(context: template.Context, url: str) -> str:
    if request := context.get("request"):
        url = URLService.update_query_parameters(
            url=url,
            parameters={"p": [request.path]},
        )
    return url


@register.simple_tag(takes_context=True)
def url_with_previous(context: template.Context, url: str, *args: Any, **kwargs: Any) -> str:
    if request := context.get("request"):
        if previous := request.GET.get("p"):
            if URLService.url_is_absolute_path(url=previous):
                return URLService.update_query_parameters(url=url, parameters={"p": [previous]})
    return url


@register.simple_tag(takes_context=True)
def link_to_previous(context: template.Context, label: str, *args: Any, **kwargs: Any) -> str:
    if request := context.get("request"):
        if url := request.GET.get("p"):
            if URLService.url_is_absolute_path(url=url):
                classes = ["btn", "btn-link"]
                # SECURITY: `classes` is safe.
                # SECURITY: `url` is escaped.
                # SECURITY: `label` is escaped.
                return mark_safe(  # nosec
                    f'<a href="{escape_uri_path(url)}" class="{" ".join(classes)}">{escape(label)}</a>'
                )
    return ""


@register.simple_tag(takes_context=True)
def input_to_previous(context: template.Context, *args: Any, **kwargs: Any) -> str:
    if request := context.get("request"):
        if url := request.GET.get("p"):
            if URLService.url_is_absolute_path(url=url):
                # SECURITY: `url` is escaped.
                return mark_safe(  # nosec
                    f'<input type="hidden" name="p" value="{escape_uri_path(url)}" />'
                )
    return ""

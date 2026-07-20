"""Render services."""

import logging
from datetime import datetime

from bs4 import BeautifulSoup
from django.utils.html import escape
from django.utils.safestring import SafeString, mark_safe
from markdown_it import MarkdownIt
from markdown_it.renderer import RendererHTML
from markdown_it.token import Token
from markdown_it.utils import EnvType, OptionsDict

from core.services import FormattingService
from webapp.services import LanguageService

logger = logging.getLogger(__name__)


_markdown_it = None


class RenderService:
    """Render service: The render service provides functions for rendering html."""

    @staticmethod
    def render_datetime(*, value: datetime) -> SafeString:
        """Renders the specified `datetime` to its safe text representation.

        Arguments:
            value: `datetime`object to render.

        Returns:
            A safe text string containing the representation of the date and
            time.
        """
        language_code = LanguageService.get_language_code()
        format_datetime = FormattingService.format_datetime(value=value, language_code=language_code)
        natural_datetime = FormattingService.natural_datetime(value=value, language_code=language_code)
        # SECURITY: Iso format of value is safe.
        # SECURITY: `format_datetime` is escaped.
        # SECURITY: `natural_datetime` is escaped.
        return mark_safe(  # nosec
            f"<time"
            f' datetime="{value.isoformat()}"'
            f' title="{escape(format_datetime)}'
            f'">{escape(natural_datetime)}</time>'
        )

    @staticmethod
    def render_markdown(*, value: str) -> SafeString:
        """Renders the specified markdown text to its safe text representation
        using HTML elements for formatting.

        Arguments:
            value: `markdown` text to render.

        Returns:
            A safe text string containing the representation of the markdown
            text formatted using HTML elements.
        """
        html = markdown_it().render(value)
        # SECURITY: Generated HTML is safe (HTML in markdown is disabled).
        return mark_safe(html)  # nosec

    @staticmethod
    def render_markdown_to_text(*, value: str) -> SafeString:
        """Renders the specified markdown text to its safe text representation
        without formatting.

        Arguments:
            value: `markdown` text to render.

        Returns:
            A safe text string containing the representation of the markdown
            text without formatting.
        """
        # Render to HTML.
        html = markdown_it().render(value)
        # Remove all HTML.
        text = BeautifulSoup(html, "html.parser").get_text()
        # SECURITY: Text is escaped after stripping HTML elements.
        return mark_safe(escape(text))  # nosec


def markdown_it() -> MarkdownIt:
    """Returns an instance of a fully configured `MarkdownIt` markdown renderer
    creating it only once per thread.
    """

    def render_link(
        renderer: RendererHTML,
        tokens: list[Token],
        idx: int,
        options: OptionsDict,
        env: EnvType,
    ) -> str:
        """Additional render rule to add a specific class to all links."""
        tokens[idx].attrSet("class", "text-light")
        return renderer.renderToken(tokens, idx, options, env)

    global _markdown_it
    if _markdown_it is None:
        _markdown_it = MarkdownIt(
            "commonmark",
            {
                "html": False,
                "breaks": True,
                "linkify": True,
            },
        ).enable("linkify")
        _markdown_it.add_render_rule("link_open", render_link)
    return _markdown_it

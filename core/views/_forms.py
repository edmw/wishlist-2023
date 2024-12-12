import logging
from html import escape
from typing import Any

from django.forms import Widget
from django.utils.safestring import SafeString, mark_safe
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)


class TextStylesMixin(Widget):
    def __init__(self, attrs: dict[str, str] | None = None):
        attrs = {"class": "form-control", **(attrs or {})}
        super().__init__(attrs)


class TextareaStylesMixin(Widget):
    def __init__(self, attrs: dict[str, str] | None = None):
        attrs = {"class": "form-control", **(attrs or {})}
        attrs["rows"] = "6"
        super().__init__(attrs)


class SelectStylesMixin(Widget):
    def __init__(self, attrs: dict[str, str] | None = None):
        attrs = {"class": "form-select", **(attrs or {})}
        super().__init__(attrs)


class RadioSelectStylesMixin(Widget):
    def __init__(self, attrs: dict[str, str] | None = None):
        attrs = {"class": "form-radio-input", **(attrs or {})}
        super().__init__(attrs)


class CheckboxStylesMixin(Widget):
    def __init__(self, attrs: dict[str, str] | None = None):
        attrs = {"class": "form-check-input", **(attrs or {})}
        super().__init__(attrs)


class PlaceholderTextMixin(Widget):
    placeholder_text = None

    def get_context(self, name: str, value: str, attrs: dict[str, str]) -> dict[str, str]:
        context = super().get_context(name, value, attrs)
        if self.placeholder_text:
            if context_widget := context.get("widget"):
                if context_attrs := context_widget.get("attrs"):
                    context_attrs["placeholder"] = _(self.placeholder_text)
        return context


class LabelBeforeMixin(Widget):
    label_text = None

    def render(
        self,
        name: str,
        value: str,
        attrs: dict[str, str] | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> SafeString:
        """Renders a label for the widget before the widget‘s markup."""
        html = super().render(name, value, attrs, *args, **kwargs)
        if self.label_text:
            if widget_id := (attrs or {}).get("id"):
                label = f'<label for="{widget_id}" class="form-label">{escape(_(self.label_text))}</label>'
                # SECURITY: `widget_id` is safe.
                # SECURITY: `label_text` is escaped.
                html = mark_safe(label) + html  # nosec
        return html


class LabelAfterMixin(Widget):
    label_text = None

    def render(
        self,
        name: str,
        value: str,
        attrs: dict[str, str] | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> SafeString:
        """Renders a label for the widget after the widget‘s markup."""
        html = super().render(name, value, attrs, *args, **kwargs)
        if self.label_text:
            if widget_id := (attrs or {}).get("id"):
                label = f'<label for="{widget_id}" class="form-label">{escape(_(self.label_text))}</label>'
                # SECURITY: `widget_id` is safe.
                # SECURITY: `label_text` is escaped.
                html = html + mark_safe(label)  # nosec
        return html


class AriaDescribedByMixin(Widget):
    def get_context(self, name: str, value: str, attrs: dict[str, str]) -> dict[str, str]:
        context = super().get_context(name, value, attrs)
        if context_widget := context.get("widget"):
            if context_attrs := context_widget.get("attrs"):
                context_attrs["aria-describedby"] = f"description_{name}"
        return context

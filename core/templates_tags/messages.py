"""The Core’s template tags for rendering messages."""

from typing import Any

from django import template
from django.contrib.messages.storage.base import Message
from django.utils.html import escape
from django.utils.safestring import SafeText, mark_safe

register = template.Library()

LEVEL_TAG_MAP_TO_CLASS = {
    "info": "info",
    "success": "success",
    "warning": "warning",
    "error": "danger",
}


@register.simple_tag(takes_context=False)
def message_style(message: Message, *args: Any, **kwargs: Any) -> SafeText:
    classes = ["alert"]
    if level_tag := message.level_tag:
        level_class = LEVEL_TAG_MAP_TO_CLASS.get(level_tag, "primary")
        classes.append(f"alert-{level_class}")
    else:
        classes.append("alert-primary")
    # SECURITY: `classes` is safe.
    return mark_safe(" ".join(classes))  # nosec


@register.simple_tag(takes_context=False)
def message_text(message: Message, *args: Any, **kwargs: Any) -> SafeText:
    text = message.message
    if isinstance(text, SafeText):
        return text
    else:
        return escape(text)

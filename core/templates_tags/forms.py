"""The Core’s template tags for rendering forms."""

from typing import Any

from django import template
from django.forms import ValidationError
from django.utils.html import escape
from django.utils.safestring import SafeText, mark_safe

register = template.Library()


@register.simple_tag(takes_context=True)
def button_to_save(context: template.Context, label: str, *args: Any, **kwargs: Any) -> SafeText:
    # SECURITY: `label` is escaped.
    return mark_safe(f'<button type="submit" class="btn btn-primary">{escape(label)}</button>')  # nosec


@register.simple_tag(takes_context=True)
def render_errors(context: template.Context, errors: list[ValidationError]) -> SafeText:
    if errors:
        errors_text = " ".join([escape(str(error)) for error in errors])
        # SECURITY: `errors` in `errors_text` are escaped.
        return mark_safe(f'<span class="text-danger">{errors_text}</span>')  # nosec
    else:
        # SECURITY: Empty string is safe.
        return mark_safe("")  # nosec

"""The Core’s template tags."""

from django import template

from .content import register as content_register
from .forms import register as forms_register
from .messages import register as messages_register
from .models import register as models_register
from .pagination import register as pagination_register

register = template.Library()

register.tags.update(content_register.tags)
register.filters.update(content_register.filters)

register.tags.update(forms_register.tags)
register.filters.update(forms_register.filters)

register.tags.update(messages_register.tags)
register.filters.update(messages_register.filters)

register.tags.update(models_register.tags)
register.filters.update(models_register.filters)

register.tags.update(pagination_register.tags)
register.filters.update(pagination_register.filters)

import uuid
from typing import Any


class UUIDFieldMixin:
    """Mixin for a UUID primary key field."""

    def __init__(self, *args: Any, **kwargs: Any):
        """Initializes the field to act as primary key using a random UUID."""
        kwargs["verbose_name"] = "id"
        kwargs["db_column"] = "id"
        kwargs["primary_key"] = True
        kwargs["default"] = uuid.uuid4
        kwargs["editable"] = False
        super().__init__(*args, **kwargs)

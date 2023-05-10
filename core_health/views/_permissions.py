"""The permissions of the Core Health application."""

from django.http import HttpRequest
from django.views import View
from rest_framework.permissions import BasePermission


class CanCheckHealth(BasePermission):
    """Permission for accessing health checks."""

    def has_permission(self, request: HttpRequest, view: View) -> bool:
        """Returns True, if the requesting user is staff and therefore has
        permission to access health checks.
        """
        if user := request.user:
            return getattr(user, "is_staff", False)
        return False

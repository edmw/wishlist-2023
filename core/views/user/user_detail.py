"""Base for all user detail views."""

import logging

from core import constants
from core.models import User
from core.views._base import DetailView
from core.views.user._base import (
    HasPermissionForUserViewMixin,
    NeedsSettingsForUserViewMixin,
)

logger = logging.getLogger(__name__)


class UserDetailView(
    HasPermissionForUserViewMixin,
    NeedsSettingsForUserViewMixin,
    DetailView,
):
    """The base view for user data."""

    http_method_names = ["get", "head", "options"]

    model = User
    pk_url_kwarg = constants.USER_ID_KEY

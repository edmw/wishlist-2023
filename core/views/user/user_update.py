"""Base for all user update views."""

import logging

from core import constants
from core.models import User
from core.views._base import UpdateView
from core.views.user._base import (
    HasPermissionForUserViewMixin,
    NeedsSettingsForUserViewMixin,
)

logger = logging.getLogger(__name__)


class UserUpdateView(
    HasPermissionForUserViewMixin,
    NeedsSettingsForUserViewMixin,
    UpdateView,
):
    """The base view to update user data."""

    http_method_names = ["get", "post", "head", "options"]

    model = User
    pk_url_kwarg = constants.USER_ID_KEY

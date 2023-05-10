"""User settings services."""
import logging

from core.models import User, UserSettings

logger = logging.getLogger(__name__)


class UserSettingsService:
    """UserSettings service: The Core’s user settings service provides functions
    for handling settings model entities and settings-related business logic.
    """

    @staticmethod
    def settings_for(*, user: User) -> UserSettings:
        """Returns the settings for the specified user.

        Creates the settings with defaults if they do not already exist.

        Arguments:
            user: User

        Returns:
            Settings for the user.
        """
        try:
            return user.settings
        except UserSettings.DoesNotExist:
            return UserSettings.objects.create(user=user)

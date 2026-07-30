"""Model class representing users.

The Core’s user model substitutes the default user model by subclassing
`AbstractUser` and adding custom attributes and behavior.
"""

import logging
from typing import Any, Iterable, override

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.base import ModelBase
from django.db.models.functions import Lower
from django.urls import reverse

from core import constants

from ._base import IDMixin
from .fields import FullnameField, LanguageField, UserIDField
from .types import Fullname, Language, UserID
from .user_settings import UserSettings

logger = logging.getLogger(__name__)


class User(IDMixin[UserID], AbstractUser):
    """Model used to represent a user persisted in database.

    Attributes:
        id: Primary key

        full_name: Full name of the user build by concatenating a user’s first
            and last name at creation or update (see signals).

        language: Code for the language the user wants to use.

        created_at: Point in time when the user was created.
        modified_at: Point in time when the user was modified.

        deprovisioned: Boolean, indicating if the user is deprovisioned.
        deprovisioned_at: point in time when the user was deprovisioned.

    Attributes (inherited):
        username: models.CharField
        first_name: models.CharField
        last_name: models.CharField
        email: models.EmailField
        is_staff: models.BooleanField
        is_active: models.BooleanField
        last_login: models.DateTimeField
    """

    class Meta:
        """Meta data for the User model."""

        verbose_name = "User"
        verbose_name_plural = "Users"

        constraints = [
            models.UniqueConstraint(Lower("username"), name="username_lower_unique"),
        ]

    class Fields:
        """Field names for the User model."""

        ID = "id_field"
        USERNAME = "username"
        FIRST_NAME = "first_name"
        LAST_NAME = "last_name"
        FULL_NAME = "full_name_field"
        EMAIL = "email"
        LANGUAGE = "language_field"
        LANGUAGE_SOFT = "language_soft_field"
        IS_STAFF = "is_staff"
        IS_ACTIVE = "is_active"
        CREATED_AT = "created_at"
        MODIFIED_AT = "modified_at"
        DEPROVISIONED = "deprovisioned"
        DEPROVISIONED_AT = "deprovisioned_at"
        LAST_LOGIN = "last_login"

    id_type = UserID
    id_field = UserIDField()

    full_name_field = FullnameField()

    @property
    def full_name(self) -> Fullname:
        """The full name for this user. This computed property returns the
        correctly typed identifier instead of an indeterminate string.

        Returns:
            The full name.
        """
        return Fullname(self.full_name_field)

    @full_name.setter
    def full_name(self, full_name: Fullname) -> None:
        """The setter for the full name of this user. This custom setter
        accepts a correctly typed identifier, only, instead of an indeterminate
        string.

        Arguments:
            full_name: The full name.
        """
        self.full_name_field = full_name

    language_field = LanguageField()

    @property
    def language(self) -> Language:
        """The language for this user. This computed property returns the
        correctly typed identifier instead of an indeterminate string.

        Returns:
            A value from the Language choices.
        """
        return Language(self.language_field)

    @language.setter
    def language(self, language: Language) -> None:
        """The setter for the language of this user. This custom setter
        accepts a correctly typed identifier, only, instead of an indeterminate
        string.

        Arguments:
            language: A value from the Language choices.
        """
        self.language_field = language

    language_soft_field = LanguageField(
        db_column="language_soft",
        verbose_name="Language (soft)",
        help_text="Language (soft) of the user",
    )

    @property
    def language_soft(self) -> Language:
        """The soft language for this user. This computed property returns the
        correctly typed identifier instead of an indeterminate string.

        Returns:
            A value from the Language choices.
        """
        return Language(self.language_soft_field)

    @language_soft.setter
    def language_soft(self, language: Language) -> None:
        """The setter for the soft language of this user. This custom setter
        accepts a correctly typed identifier, only, instead of an indeterminate
        string.

        Arguments:
            language: A value from the Language choices.
        """
        self.language_soft_field = language

    # Relations

    settings: UserSettings

    # Lifecycle

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    deprovisioned = models.BooleanField(
        default=False,
        verbose_name="deprovisioned",
        help_text=(
            "Designates whether this user should be treated as deleted. Use "
            "this instead of actually deleting users."
        ),
    )
    deprovisioned_at = models.DateTimeField(blank=True, null=True)

    @classmethod
    def create(
        cls,
        user_id: UserID,
        username: str,
        first_name: str,
        last_name: str,
    ) -> User:
        """Create a user model instance without persisting it.

        Arguments:
            user_id: The identifier for the new user.
            username: Username for the new user.
            first_name: First name for the new user.
            last_name: Last name for the new user.

        Returns:
            User instance created.
        """
        return cls(
            id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            name=f"{first_name} {last_name}",
        )

    @override
    def save(
        self,
        *args: Any,
        force_insert: bool | tuple[ModelBase, ...] = False,
        force_update: bool = False,
        using: str | None = None,
        update_fields: Iterable[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """Save the current instance.

        Updates the user’s full name to the concatenation of first name and last
        name at the beginning of a user’s save.
        """
        from core.services import UserService

        self.full_name = UserService.full_name_for(user=self)

        if update_fields is not None:
            update_fields = {User.Fields.FULL_NAME}.union(update_fields)
        super().save(
            *args,
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
            **kwargs,
        )

    def __repr__(self) -> str:
        """Returns a string reputation of this user.

        Returns:
            Reputation text.
        """
        return f"<{self.__class__.__name__}: {self.username}; {str(self.id)}>"

    # Custom properties

    @property
    def is_modified(self) -> bool:
        """Flag to indicate if this user was modified after creation.

        Returns:
            True, if this user was modified.
        """
        return self.modified_at.replace(microsecond=0) > self.created_at.replace(microsecond=0)

    def get_language(self) -> Language:
        """Returns the language for this user.

        Takes into account an explicitly set language as well as a language that
        may have been implicitly determined. The language english is taken as
        the default as the last resort.

        Returns:
            Language
        """
        if self.language:
            return self.language
        if self.language_soft:
            return self.language_soft
        return Language("en")

    def get_absolute_url(self) -> str:
        """Returns the URL for the page to view this user.

        Returns:
            URL
        """
        return reverse(
            constants.VIEW_USER_PROFILE,
            kwargs={constants.USER_ID_KEY: self.pk},
        )

    def get_absolute_edit_url(self) -> str:
        """Returns the URL for the page to edit this user.

        Returns:
            URL
        """
        return reverse(
            constants.VIEW_USER_PROFILE_UPDATE,
            kwargs={constants.USER_ID_KEY: self.pk},
        )

    def get_absolute_settings_url(self) -> str:
        """Returns the URL for the page to view this user’s settings.

        Returns:
            URL
        """
        return reverse(
            constants.VIEW_USER_SETTINGS,
            kwargs={constants.USER_ID_KEY: self.pk},
        )

    def get_absolute_settings_edit_url(self) -> str:
        """Returns the URL for the page to edit this user’s settings.

        Returns:
            URL
        """
        return reverse(
            constants.VIEW_USER_SETTINGS_UPDATE,
            kwargs={constants.USER_ID_KEY: self.pk},
        )

    def get_absolute_lists_url(self) -> str:
        """Returns the URL for the page to view this user’s wish lists.

        Returns:
            URL
        """
        return reverse(
            constants.VIEW_LISTS,
            kwargs={constants.USER_ID_KEY: self.pk},
        )

    def get_absolute_favorites_url(self) -> str:
        """Returns the URL for the page to view this user’s favorites.

        Returns:
            URL
        """
        return reverse(
            constants.VIEW_FAVORITES,
            kwargs={constants.USER_ID_KEY: self.pk},
        )

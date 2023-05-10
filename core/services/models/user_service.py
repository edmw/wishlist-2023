"""User services."""

import logging
from typing import Iterator

from django.core.exceptions import ObjectDoesNotExist

from core.models import Fullname, User, UserID

logger = logging.getLogger(__name__)


class UserService:
    """User service: The Core’s user service provides functions for handling
    user model entities and user-related business logic.
    """

    @staticmethod
    def get_users_iterator(*, chunk_size: int = 2000) -> Iterator[User]:
        """Returns an iterator over all users in the database.

        Arguments:
            chunk_size: Specifies the number of results to cache at the database
            level. Fetching bigger chunks diminishes the number of round trips
            to the database.

        Returns:
            An iterator.
        """
        users = User.objects.all().iterator(chunk_size=chunk_size)
        return users

    @staticmethod
    def get_user(id: UserID) -> User:
        """Gets the user with the matching id. Raises an `User.DoesNotExist`
        exception if a user with the specified ID does not exist.

        Arguments:
            id: The user’s identifier to look up.

        Returns:
            A user entity.

        Raises:
            User.DoesNotExist
        """
        user = User.objects.get(id_field=id)
        return user

    @staticmethod
    def find_user_for_username(*, username: str) -> User | None:
        """Finds the user with the matching username. Search is case-insensitive.
        Returns `None` if a user with the specified username does not exist.

        Arguments:
            id: The user’s name to look up.

        Returns:
            A user entity or None
        """
        try:
            return User.objects.get(username__iexact=username)
        except ObjectDoesNotExist:
            return None

    @staticmethod
    def find_user_for_email(*, email: str) -> User | None:
        """Finds the user with the matching email. Search is case-insensitive.
        Returns `None` if a user with the specified email does not exist.

        Arguments:
            id: The user’s email to look up.

        Returns:
            A user entity or None
        """
        try:
            return User.objects.get(email__iexact=email)
        except ObjectDoesNotExist:
            return None

    @staticmethod
    def full_name_for(*, user: User) -> Fullname:
        """Builds the full name for the specified user using the concatenation
        of first name and last name.

        Arguments:
            user: The user entity to build the full name for.

        Returns:
            A string containing the user’s full name.
        """
        if user.first_name and user.last_name:
            return Fullname(f"{user.first_name} {user.last_name}")
        else:
            string = user.first_name if user.first_name else user.last_name
            return Fullname(string)

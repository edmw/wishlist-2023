"""Wish services."""

import logging

from django.utils import timezone

from core.models import Wish, WishID, WishLens

logger = logging.getLogger(__name__)


class WishServiceError(Exception):
    pass


class WishNotArchivableError(WishServiceError):
    pass


class WishNotUnarchivableError(WishServiceError):
    pass


class WishService:
    """Wish service: The Core’s wish service provides functions for handling
    wish model entities and wish-related business logic.
    """

    @staticmethod
    def get_wish(id: WishID) -> Wish:
        """Gets the wish with the matching id. Raises an `Wish.DoesNotExist`
        exception if a wish with the specified ID does not exist.

        Arguments:
            id: The wish’s identifier to look up.

        Returns:
            A wish entity.

        Raises:
            Wish.DoesNotExist
        """
        return WishLens.view().queryset.get(id_field=id)

    @staticmethod
    def archive(*, wish: Wish, save: bool = True) -> None:
        """Archives the specified wish.

        Arguments:
            wish: Wish to archive.
            save: Flag, if the archived wish should be saved.

        Raises:
            WishNotArchivableError: If the specified wish can not be archived.
        """
        if wish.archivable:
            wish.archived = True
            wish.archived_at = timezone.now()
            if save:
                wish.save(update_fields=[Wish.Fields.ARCHIVED, Wish.Fields.ARCHIVED_AT])
        else:
            raise WishNotArchivableError()

    @staticmethod
    def unarchive(*, wish: Wish, save: bool = True) -> None:
        """Unarchives the specified wish.

        Arguments:
            wish: Wish to unarchive.
            save: Flag, if the unarchived wish should be saved.

        Raises:
            WishNotUnarchivableError: If the specified wish can not be
                unarchived.
        """
        if wish.archived:
            wish.archived = False
            wish.archived_at = None
            if save:
                wish.save(update_fields=[Wish.Fields.ARCHIVED, Wish.Fields.ARCHIVED_AT])
        else:
            raise WishNotUnarchivableError()

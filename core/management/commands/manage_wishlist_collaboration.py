"""Wishlist collaboration command."""

from argparse import ArgumentError
from typing import Any

from django.core.management.base import CommandError, CommandParser

from core.models import User, UserID, WishlistID
from core.services import (
    UserService,
    WishlistCollaborationOwnerAsEditorError,
    WishlistCollaborationPrivateWishlistError,
    WishlistCollaborationService,
    WishlistService,
)

from ._base import CoreBaseCommand


class Command(CoreBaseCommand):
    """Manage wishlist collaboration memberships for editors."""

    help = "Adds or removes a user as editor for a wishlist."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "action",
            choices=["add-editor", "remove-editor"],
            help="Operation to execute.",
        )
        parser.add_argument(
            "--wishlist-id",
            required=True,
            type=self.id_argument(WishlistID),
            metavar="ID",
            help="ID of the wishlist (UUID or base62 UUID).",
        )

        user_group = parser.add_mutually_exclusive_group(required=True)
        user_group.add_argument(
            "--user-id",
            type=self.id_argument(UserID),
            metavar="ID",
            help="ID of the user (UUID or base62 UUID).",
        )
        user_group.add_argument(
            "--user-email",
            metavar="EMAIL",
            help="Email address of the user.",
        )

        return super().add_arguments(parser)

    def handle(self, *args: Any, **options: Any) -> None:
        super().handle(*args, **options)

        action = options.get("action")
        wishlist_id = options.get("wishlist_id")
        if not action or not wishlist_id:
            raise ArgumentError(None, "Action and wishlist ID are required.")

        wishlist = WishlistService.get_wishlist(id=wishlist_id)
        user = self.resolve_user(options=options)

        try:
            match action:
                case "add-editor":
                    created = WishlistCollaborationService.add_editor(wishlist=wishlist, user=user)
                    if created:
                        self.print(f"Added editor {user.email} to wishlist {wishlist.id}.")
                    else:
                        self.print(f"Editor {user.email} is already assigned to wishlist {wishlist.id}.")
                case "remove-editor":
                    deleted = WishlistCollaborationService.remove_editor(wishlist=wishlist, user=user)
                    if deleted:
                        self.print(f"Removed editor {user.email} from wishlist {wishlist.id}.")
                    else:
                        self.print(f"Editor {user.email} was not assigned to wishlist {wishlist.id}.")
                case _:
                    raise ArgumentError(None, "Unsupported action.")
        except WishlistCollaborationPrivateWishlistError as error:
            raise CommandError("Cannot add collaborators to private wishlists.") from error
        except WishlistCollaborationOwnerAsEditorError as error:
            raise CommandError("Wishlist owner cannot be added as editor.") from error

    def resolve_user(self, *, options: dict[str, Any]) -> User:
        user_id = options.get("user_id")
        if user_id:
            return UserService.get_user(id=user_id)

        user_email = options.get("user_email")
        if not user_email:
            raise ArgumentError(None, "Either user ID or user email is required.")

        users = User.objects.filter(email__iexact=user_email)
        if users.count() != 1:
            raise CommandError(
                f"Expected exactly one user for email '{user_email}', found {users.count()}."
            )

        return users.get()

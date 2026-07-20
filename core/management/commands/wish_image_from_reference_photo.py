"""Wish generate image command."""

import textwrap
from argparse import ArgumentError
from typing import Any

from celery import exceptions as celery_exceptions
from django.core.management.base import CommandParser

from core.models import WishID, WishLens
from core.models.types.wishlist_id import WishlistID
from core.services import WishlistService, WishService
from core.tasks.wish import generate_image_for_reference_photo

from ._base import CoreBaseCommand


class Command(CoreBaseCommand):
    """Wish generate image command: Generates images for wishes from reference photo."""

    help = "Generates images for wishes from reference photos."

    def add_arguments(self, parser: CommandParser) -> None:
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "--wish-id",
            type=self.id_argument(WishID),
            metavar="ID",
            help=(
                "ID of the wish for which the image is to be created from the "
                "reference photo. Does nothing if no reference photo is stored "
                "for the wish. ID is either the UUID for the wish or the "
                "base62 encoded UUID."
            ),
        )
        group.add_argument(
            "--wishlist-id",
            metavar="ID",
            type=self.id_argument(WishlistID),
            help=(
                "ID of the wishlist for whose wishes the images are to be "
                "created from the reference photos. Does nothing if no "
                "reference photos are stored for the wishes. ID is either "
                "the UUID for the wishlist or the base62 encoded UUID."
            ),
        )
        group.add_argument(
            "--all",
            action="store_true",
            help=(
                "Generates images for all wishes from their reference photos. "
                "Does nothing if no eference photos are stored for the wishes."
            ),
        )

        parser.add_argument(
            "--foreground",
            action="store_true",
            help="Executes in foreground instead utilizing background workers.",
        )
        return super().add_arguments(parser)

    def handle(self, *args: Any, **options: Any) -> None:
        super().handle(*args, **options)

        self.banner(["WISH IMAGE FROM REFERENCE PHOTO", *textwrap.wrap(self.help)])

        if options.get("all"):
            wishes = WishLens().queryset.all()
        elif wish_id := options.get("wish_id"):
            wishes = [WishService.get_wish(id=wish_id)]
        elif wishlist_id := options.get("wishlist_id"):
            wishlist = WishlistService.get_wishlist(id=wishlist_id)
            wishes = WishLens().by_wishlist(list=wishlist).queryset.all()
        else:
            raise ArgumentError(None, "No wishes specified.")

        foreground = options.get("foreground", False)

        for wish in wishes:
            if foreground:
                try:
                    generate_image_for_reference_photo(wish_id=wish.id)
                except celery_exceptions.Retry:
                    # Retry is not an error, so ignore it. If running in
                    # foreground the will no retry, intentionally.
                    pass
            else:
                self.print(f"Scheduling: Wish {wish!r}")
                generate_image_for_reference_photo.apply_async(
                    kwargs={
                        "wish_id": wish.id,
                    },
                )

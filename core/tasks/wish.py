from celery import Task, shared_task
from celery.exceptions import MaxRetriesExceededError
from celery.utils.log import get_task_logger
from django.conf import settings as django_settings
from django.utils.translation import gettext as _

from core.models import FavoriteLens, WishID
from core.services import (
    ImageService,
    ImageServiceRetrieveConnectionError,
    ImageServiceRetrieveTimeoutError,
    ImageServiceUnidentifiedImageError,
    NotificationService,
    WishService,
)
from webapp.services import LanguageService, TaskLoggingService

logger = get_task_logger(__name__)


@shared_task(
    name="Wish-Notify-On-Create",
    bind=True,
)
def notify_on_create(self: Task, wish_id: WishID) -> bool:
    """Task to notify the users about the creation of a new wish on a wish list,
    if they have this wish list in their favorites.

    Arguments:
        self: Actual task instance
        wish_id: The identifier for the wish which was reserved.
    """
    TaskLoggingService.task_begin("Sending Notification for created Wish <%s>", wish_id, logger=logger)

    wish = WishService.get_wish(id=wish_id)
    wishlist = wish.wishlist

    for favorite in FavoriteLens.view().by_wishlist(wishlist=wishlist).for_iterating().qs():
        if favorite.notify_on_item_create:
            user = favorite.user
            with LanguageService.activated(language_code=user.get_language().get_code()):
                NotificationService.send(
                    user=user,
                    subject=_("Wish added"),
                    template_name="item/notifications/create.txt",
                    html_template_name="item/notifications/create.html",
                    simple_html_template_name="item/notifications/create_simple.html",
                    context={
                        "wish_name": wish.name,
                        "wishlist_name": wishlist.name,
                    },
                )

    TaskLoggingService.task_end("Sending Notification for created Wish <%s>", wish_id, logger=logger)

    return True


@shared_task(
    name="Wish-Notify-On-Reservation-Create",
    bind=True,
)
def notify_on_reservation_create(self: Task, wish_id: WishID) -> bool:
    """Task to notify the owner of a wish list when a wish has been reserved on
    that wish list.

    Arguments:
        self: Actual task instance
        wish_id: The identifier for the wish which was reserved.
    """
    TaskLoggingService.task_begin(
        "Sending Notification for created Reservation on Wish <%s>", wish_id, logger=logger
    )

    wish = WishService.get_wish(id=wish_id)
    wishlist = wish.wishlist
    owner = wishlist.owner

    with LanguageService.activated(language_code=owner.get_language().get_code()):
        NotificationService.send(
            user=owner,
            subject=_("Wish reserved"),
            template_name="reservation/notifications/create.txt",
            html_template_name="reservation/notifications/create.html",
            simple_html_template_name="reservation/notifications/create_simple.html",
            context={
                "wish_name": wish.name,
                "wishlist_name": wishlist.name,
                "wishlist_masked": wishlist.mask_reservations,
            },
        )

    TaskLoggingService.task_end(
        "Sending Notification for created Reservation on Wish <%s>", wish_id, logger=logger
    )

    return True


@shared_task(
    name="Wish-Notify-On-Reservation-Delete",
    bind=True,
)
def notify_on_reservation_delete(self: Task, wish_id: WishID) -> bool:
    """Task to notify the owner of a wish list when the reservation of a wish
    has been deleted on this wish list.

    Arguments:
        self: Actual task instance
        wish_id: The identifier for the wish which was reserved.
    """
    TaskLoggingService.task_begin(
        "Sending Notification for deleted Reservation on Wish <%s>", wish_id, logger=logger
    )

    wish = WishService.get_wish(id=wish_id)
    wishlist = wish.wishlist
    owner = wishlist.owner

    with LanguageService.activated(language_code=owner.get_language().get_code()):
        NotificationService.send(
            user=owner,
            subject=_("Wish released"),
            template_name="reservation/notifications/delete.txt",
            html_template_name="reservation/notifications/delete.html",
            simple_html_template_name="reservation/notifications/delete_simple.html",
            context={
                "wish_name": wish.name,
                "wishlist_name": wishlist.name,
                "wishlist_masked": wishlist.mask_reservations,
            },
        )

    TaskLoggingService.task_end(
        "Sending Notification for deleted Reservation on Wish <%s>", wish_id, logger=logger
    )

    return True


@shared_task(
    name="Wish-Generate-Image-Reference-Photo",
    bind=True,
    max_retries=3,
    default_retry_delay=3,
)
def generate_image_from_reference_photo(self: Task, wish_id: WishID) -> bool:
    """Task to generate an image if the web reference to a wish‘s photo has
    been changed.

    Arguments:
        self: Actual task instance
        wish_id: The identifier for the wish.
    """
    TaskLoggingService.task_begin(
        "Updating Image for Reference Photo for Wish <%s>", wish_id, logger=logger
    )

    wish = WishService.get_wish(id=wish_id)
    if reference_photo := wish.reference_photo:
        try:
            image = ImageService.generate_jpeg_image_from_url(
                url=reference_photo,
                max_image_pixels=django_settings.WISH_IMAGE_PIXELS_MAX,
            )
            wish.image_field.update(name=reference_photo, image=image)
        except ImageServiceUnidentifiedImageError:
            TaskLoggingService.task_fail(
                "Unidentified image while retrieving image for Reference Photo",
                logger=logger,
                data={"wish.id": str(wish_id), "image.url": reference_photo},
            )
        except (ImageServiceRetrieveTimeoutError, ImageServiceRetrieveConnectionError):
            try:
                TaskLoggingService.task_retry(
                    "Timeout while retrieving image for Reference Photo",
                    logger=logger,
                    data={
                        "wish.id": str(wish.id),
                        "reference_photo": reference_photo,
                    },
                )
                raise self.retry()
            except MaxRetriesExceededError:
                TaskLoggingService.task_fail(
                    "Maximum retries exeeded while retrieving image for Reference Photo",
                    logger=logger,
                    data={"wish.id": str(wish_id), "image.url": reference_photo},
                )

    TaskLoggingService.task_end("Updating Image for Reference Photo for Wish <%s>", wish_id, logger=logger)

    return True

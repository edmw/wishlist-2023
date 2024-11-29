"""The Core’s template tags for rendering content."""

from django import template
from django.templatetags.static import static
from django.utils.safestring import SafeText, mark_safe
from django.utils.translation import gettext as _

from core.models import Wish

register = template.Library()


#  ##      ## ####  ######  ##     ##
#  ##  ##  ##  ##  ##    ## ##     ##
#  ##  ##  ##  ##  ##       ##     ##
#  ##  ##  ##  ##   ######  #########
#  ##  ##  ##  ##        ## ##     ##
#  ##  ##  ##  ##  ##    ## ##     ##
#   ###  ###  ####  ######  ##     ##


@register.simple_tag
def wish_image(wish: Wish) -> SafeText:
    if wish.image_field:
        # SECURITY: Image url is safe (internal).
        return mark_safe(f'<img src="{ wish.image_field.url }" />')  # nosec
    else:
        gift = static("core/icons/gift.svg")
        # SECURITY: `gift` is safe.
        return mark_safe(f'<img src="{gift}" class="placeholder">')  # nosec


@register.simple_tag
def wish_preference(wish: Wish) -> SafeText:
    number_of_hearts = int(wish.preference) + 3
    # SECURITY: There is nothing unsafe.
    return mark_safe(number_of_hearts * "♥")  # nosec


@register.simple_tag
def wish_status(wish: Wish, mask_reservations: bool) -> SafeText:
    if wish.is_received:
        status = _("received")
    else:
        if mask_reservations:
            status = "???"
        else:
            if wish.is_reserved:
                status = _("reserved")
            else:
                status = _("wanted")
    # SECURITY: `status` is safe.
    return mark_safe(status)  # nosec

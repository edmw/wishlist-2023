import logging
from typing import Any, cast

from django.contrib import messages
from django.db.models import QuerySet
from django.forms import ChoiceField, EmailField, EmailInput, Form, ModelForm, RadioSelect
from django.http import HttpResponse
from django.http.response import HttpResponseRedirect
from django.utils.translation import gettext as _
from django.utils.translation import gettext_noop

from core.apps import CoreConfig
from core.models import Wishlist, WishlistInvitation, WishlistLens
from core.models.types import InvitationVariant
from core.services import (
    InvitationAccessClosedError,
    InvitationLimitExceededError,
    InvitationPrivateWishlistError,
    InvitationService,
)
from core.views._base import LoginRequiredMixin, UpdateView, WishlistModelMixin
from core.views._forms import (
    AriaDescribedByMixin,
    LabelBeforeMixin,
    PlaceholderTextMixin,
    RadioSelectStylesMixin,
    TextStylesMixin,
)

from ._base import HasPermissionForListViewMixin

logger = logging.getLogger(__name__)


class ShareEmailWidget(  # pyright: ignore[reportIncompatibleVariableOverride]
    LabelBeforeMixin,
    PlaceholderTextMixin,
    AriaDescribedByMixin,
    TextStylesMixin,
    EmailInput,
):
    placeholder_text = gettext_noop("Enter email")


class ShareVariantWidget(  # pyright: ignore[reportIncompatibleMethodOverride, reportIncompatibleVariableOverride]  # noqa: E501
    LabelBeforeMixin,
    AriaDescribedByMixin,
    RadioSelectStylesMixin,
    RadioSelect,
):
    label_text = gettext_noop("Type of invitation")


class ShareEmailField(EmailField):
    widget = ShareEmailWidget


class ListShareForm(Form):
    email = ShareEmailField(required=True)
    variant = ChoiceField(
        choices=InvitationVariant.VARIANTS,
        initial=InvitationVariant.NOTIFY,
        widget=ShareVariantWidget,
    )

    def __init__(self, *args: Any, **kwargs: Any):
        self.instance = kwargs.pop("instance")
        super().__init__(*args, **kwargs)


class ListShareView(
    LoginRequiredMixin,
    HasPermissionForListViewMixin,
    WishlistModelMixin,
    UpdateView,
):
    http_method_names = ["get", "post", "head", "options"]

    page_title = gettext_noop("Share your List")
    form_title = gettext_noop("Share List")
    form_class = ListShareForm
    template_name = "list/list_share.html"

    success_url = "/"
    success_message = gettext_noop("An invitation for sharing your wish list has been successfully sent.")
    error_message_private_wishlist = gettext_noop(
        "Private wish lists cannot be shared. Please change the visibility of the list before you share it."
    )
    error_message_access_closed = gettext_noop(
        "Invitations are currently not possible. Please try again later."
    )
    error_message_limit_exceeded = gettext_noop(
        "You have reached the daily limit of invitations. Please try again tomorrow."
    )

    def get_queryset(self) -> QuerySet[Wishlist]:
        user = self.try_user()
        return WishlistLens.view().by_owner(user=user).queryset

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        # The expiry duration is passed in seconds and humanized by the template
        # filter in the active language, so that it matches what the invitee
        # will see in the invitation email.
        context["expires_after"] = WishlistInvitation.expires_after_seconds()
        return context

    def form_valid(self, form: ModelForm) -> HttpResponse:
        wishlist = cast(Wishlist, self.get_object())
        email = str(form.cleaned_data["email"])
        variant = InvitationVariant(str(form.cleaned_data["variant"]))
        try:
            invitation = InvitationService.create_invitation(
                wishlist=wishlist,
                inviter=self.try_user(),
                invitee_email=email,
                variant=variant,
                access=CoreConfig.access,
            )
            InvitationService.send_invitation(invitation=invitation)
        except InvitationPrivateWishlistError:
            logger.warning("Invitation for private wish list %r requested.", wishlist.id)
            return self.redirect_back_with_error_message(_(self.error_message_private_wishlist))
        except InvitationAccessClosedError:
            logger.info("Invitation for wish list %r rejected; the access mode is closed.", wishlist.id)
            return self.redirect_back_with_error_message(_(self.error_message_access_closed))
        except InvitationLimitExceededError:
            logger.info("Invitation for wish list %r rejected; the daily limit was reached.", wishlist.id)
            return self.redirect_back_with_error_message(_(self.error_message_limit_exceeded))

        if message := getattr(self, "success_message", None):
            messages.success(self.request, _(message))
        return HttpResponseRedirect(self.get_success_url())

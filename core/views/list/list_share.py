import logging
from typing import Any, cast

from django.contrib import messages
from django.db.models import QuerySet
from django.forms import EmailField, EmailInput, Form, ModelForm
from django.http import HttpResponse
from django.http.response import HttpResponseRedirect
from django.utils.translation import gettext as _
from django.utils.translation import gettext_noop

from core.models import Wishlist, WishlistInvitation, WishlistLens
from core.services import InvitationPrivateWishlistError, InvitationService, TemplatedNotification
from core.views._base import LoginRequiredMixin, UpdateView, WishlistModelMixin
from core.views._forms import (
    AriaDescribedByMixin,
    LabelBeforeMixin,
    PlaceholderTextMixin,
    TextStylesMixin,
)

from ._base import HasPermissionForListViewMixin

logger = logging.getLogger(__name__)

INVITATION_EMAIL = TemplatedNotification(
    subject=gettext_noop("Invitation to a wish list"),
    template_name="email/invitation_wishlist.txt",
    html_template_name="email/invitation_wishlist.html",
)


class ShareEmailWidget(
    LabelBeforeMixin,
    PlaceholderTextMixin,
    AriaDescribedByMixin,
    TextStylesMixin,
    EmailInput,
):
    placeholder_text = gettext_noop("Enter email")


class ShareEmailField(EmailField):
    widget = ShareEmailWidget


class ListShareForm(Form):
    email = ShareEmailField(required=True)

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
        try:
            invitation = InvitationService.create_invitation(
                wishlist=wishlist,
                inviter=self.try_user(),
                invitee_email=email,
            )
            InvitationService.send_invitation(invitation=invitation, email=INVITATION_EMAIL)
        except InvitationPrivateWishlistError:
            logger.warning("Invitation for private wish list %r requested.", wishlist.id)
            return self.redirect_back_with_error_message(_(self.error_message_private_wishlist))

        if message := getattr(self, "success_message", None):
            messages.success(self.request, _(message))
        return HttpResponseRedirect(self.get_success_url())

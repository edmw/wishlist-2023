from typing import Protocol

from django.conf import settings as django_settings
from django.urls import reverse

from core import constants
from core.models.types import InvitationCode


class HasCode(Protocol):
    code: InvitationCode


class InvitationURLsMixin:
    def get_absolute_accept_url(self: HasCode) -> str:
        """Returns the absolute URL for accepting this invitation.

        The URL contains the invitation's code so that the invitation is
        automatically marked as accepted after its first use (see ADR-1000).
        Unlike the other `get_absolute_*_url` methods, this returns a fully
        qualified URL including the webapp location, because it is used in
        emails sent to external recipients.

        Returns:
            Absolute URL for accepting the invitation.
        """
        path = reverse(
            constants.VIEW_INVITATION_ACCEPT,
            kwargs={constants.INVITATION_CODE_KEY: str(self.code)},
        )
        return f"{django_settings.WEBAPP_LOCATION}{path}"

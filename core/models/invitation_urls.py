from django.conf import settings as django_settings
from django.urls import reverse

from core import constants


class InvitationURLsMixin:
    def get_absolute_accept_url(self, *, token: str) -> str:
        """Returns the absolute URL for accepting this invitation.

        The URL contains the plaintext invitation token; only a hash of it is
        stored in the database (see REQ-2.17). Unlike the other
        `get_absolute_*_url` methods, this returns a fully qualified URL
        including the webapp location, because it is used in emails sent to
        external recipients.

        Arguments:
            token: The plaintext invitation token to embed in the link. It is
                only available on freshly created instances (see `token`).

        Returns:
            Absolute URL for accepting the invitation.
        """
        path = reverse(
            constants.VIEW_INVITATION_ACCEPT,
            kwargs={constants.INVITATION_CODE_KEY: token},
        )
        return f"{django_settings.WEBAPP_LOCATION}{path}"

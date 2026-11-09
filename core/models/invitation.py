"""Model class representing a general invitation."""

from __future__ import annotations

import hashlib
import logging
from collections.abc import Iterable
from typing import Any, override

from django.conf import settings as django_settings
from django.db import models

from core.models import fields, types
from core.models._base import IDMixin

logger = logging.getLogger(__name__)


class Invitation(
    IDMixin[types.InvitationID],
    models.Model,
):
    """Abstract model used to represent a general invitation persisted in
    database.

    Only a hash of the random token is stored (see `code`); the plaintext
    token exists transiently on freshly created instances (see `token`) and
    in the link that was sent to the invitee.
    """

    id_type = types.InvitationID
    id_field = fields.InvitationIDField()

    inviter = models.ForeignKey(
        django_settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="%(class)ss",
    )
    inviter_id: types.UserID

    invitee_email_field = fields.InvitationEmailField()

    code_field = fields.InvitationCodeField()

    state_field = fields.InvitationStateField()

    # Lifecycle

    created_at = models.DateTimeField(auto_now_add=True)

    sent_at = models.DateTimeField(blank=True, null=True)
    accepted_at = models.DateTimeField(blank=True, null=True)
    declined_at = models.DateTimeField(blank=True, null=True)
    revoked_at = models.DateTimeField(blank=True, null=True)

    # The plaintext token is not persisted; it exists only on instances that
    # were created in this process and have not been sent yet.
    _token: str | None = None

    class Meta:
        """Meta data for the abstract Invitation model."""

        abstract = True

        verbose_name = "Invitation"
        verbose_name_plural = "Invitations"

    class Fields:
        """Field names for the Invitation model."""

        ID = "id_field"
        INVITER = "inviter"
        INVITEE_EMAIL = "invitee_email_field"
        CODE = "code_field"
        STATE = "state_field"
        CREATED_AT = "created_at"
        SENT_AT = "sent_at"
        ACCEPTED_AT = "accepted_at"
        DECLINED_AT = "declined_at"
        REVOKED_AT = "revoked_at"

    # Concerns

    def __str__(self) -> str:
        """Returns a string representation of this invitation.

        Returns:
            Representation text.
        """
        return f"{self.inviter_id}"

    def __repr__(self) -> str:
        """Returns a string reputation of this reservation.

        Returns:
            Reputation text.
        """
        return f"<{self.__class__.__name__}[{str(self.id)}]: inviter={self.inviter_id};>"

    # Properties

    @property
    def code(self) -> types.InvitationCode:
        """The hash of the invitation token. This computed property returns
        the correctly typed value instead of an indeterminate string. Only
        this hash is persisted; the plaintext token must never be stored.

        Returns:
            The hash of the invitation token.
        """
        return types.InvitationCode(self.code_field)

    @code.setter
    def code(self, code: types.InvitationCode) -> None:
        """The setter for the hash of the invitation token. This custom setter
        accepts a correctly typed value, only, instead of an indeterminate
        string.

        Arguments:
            code: The hash of the invitation token.
        """
        self.code_field = code

    @property
    def token(self) -> str | None:
        """The plaintext invitation token, if it is still available.

        Only a hash of the token is persisted; the plaintext exists transiently
        on instances that were just created and not yet sent, so that the link
        can be built for delivery. Once an instance has been loaded from the
        database again, only its hash is known and this returns `None`.

        Returns:
            The plaintext token, or `None` if it is no longer available.
        """
        return self._token

    @property
    def invitee_email(self) -> types.InvitationEmail:
        """The email address for the invitee of this invitation. This computed
        property returns the correctly typed value instead of an indeterminate
        string. Every invitation addresses exactly one email address.

        Returns:
            The email address of the invitee.
        """
        return types.InvitationEmail(self.invitee_email_field)

    @invitee_email.setter
    def invitee_email(self, invitee_email: types.InvitationEmail) -> None:
        """The setter for the email address of the invitee. This custom setter
        accepts a correctly typed value, only, instead of an indeterminate
        string.

        Arguments:
            invitee_email: The email address of the invitee.
        """
        self.invitee_email_field = str(invitee_email)

    @property
    def state(self) -> types.InvitationState:
        """The current state of this invitation.

        `EXPIRED` is derived at read time: an invitation in one of the open
        states (`CREATED`, `PENDING`) that has passed its expiration duration
        reports as `EXPIRED`. The stored value never changes because of time,
        and final states are reported as stored (see REQ-2.25/REQ-2.26).

        Returns:
            The current state.
        """
        if self.state_field in types.InvitationState.OPEN_STATES and self.expired:
            return types.InvitationState(types.InvitationState.EXPIRED)
        return types.InvitationState(self.state_field)

    # Custom properties

    @property
    def expired(self) -> bool:
        # Indicates whether this invitation has been expired after creation.
        raise NotImplementedError("The expired property must be implemented!")

    @override
    def refresh_from_db(
        self,
        *args: Any,
        using: str | None = None,
        fields: Iterable[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """Reloads the field values of this instance from the database.

        The plaintext token is not persisted; once the instance has been reloaded, only its hash
        is known again, so any transient token held on the instance is dropped (see `token`).
        """
        super().refresh_from_db(*args, using=using, fields=fields, **kwargs)
        self._token = None

    # Custom methods

    def was_accepted(self) -> None:
        # A function called after this invitation has been accepted.
        raise NotImplementedError("The was_accepted method must be implemented!")

    @staticmethod
    def hash_token(token: str) -> types.InvitationCode:
        """Returns the SHA-256 hash of an invitation token.

        The hex-encoded digest is what gets persisted in `code_field`; the
        plaintext token itself must never be stored (see REQ-2.17).

        Arguments:
            token: The plaintext invitation token to hash.

        Returns:
            The SHA-256 hash of the token, typed as an invitation code.
        """
        return types.InvitationCode(hashlib.sha256(token.encode("utf-8")).hexdigest())

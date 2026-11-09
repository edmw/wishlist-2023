from django.utils.translation import gettext_lazy


class InvitationState(str):
    """Model field type for the state of an invitation.

    Specifies the valid states, which of them can be stored in the database,
    and a default. `EXPIRED` is derived at read time from one of the open
    states plus the configured expiration duration; it is never stored.
    """

    CREATED = "created"
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"
    REVOKED = "revoked"

    STATES = [
        (CREATED, gettext_lazy("Created")),
        (PENDING, gettext_lazy("Pending")),
        (ACCEPTED, gettext_lazy("Accepted")),
        (DECLINED, gettext_lazy("Declined")),
        (EXPIRED, gettext_lazy("Expired")),
        (REVOKED, gettext_lazy("Revoked")),
    ]
    STATES_DICT = dict(STATES)

    # The states that can actually be stored in the database. `EXPIRED` is
    # derived and must never be written to the state field; it is therefore
    # not part of the choices offered for the field.
    STORED_STATES = (CREATED, PENDING, ACCEPTED, DECLINED, REVOKED)

    choices = [
        (CREATED, gettext_lazy("Created")),
        (PENDING, gettext_lazy("Pending")),
        (ACCEPTED, gettext_lazy("Accepted")),
        (DECLINED, gettext_lazy("Declined")),
        (REVOKED, gettext_lazy("Revoked")),
    ]

    # The open states from which an invitation can still become `EXPIRED`.
    OPEN_STATES = (CREATED, PENDING)

    # The final states: once reached, the state never changes again.
    FINAL_STATES = (ACCEPTED, DECLINED, EXPIRED, REVOKED)

    max_length = 16
    default = CREATED

    @property
    def display(self) -> str:
        """Returns a string that can be used for display in the UI.

        Returns:
            String for display use.
        """
        return str(self.STATES_DICT.get(self, ""))

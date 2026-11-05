"""The Core’s access modes."""

from enum import StrEnum


class CoreAccess(StrEnum):
    """Specifies who may create an account in this application.

    * `PUBLIC` -- sign-up is open to everyone.
    * `EXISTING` -- only existing users can participate; new accounts are
        created on the basis of an invitation (see ADR-1000).
    * `NOBODY` -- no new accounts can be created at all, not even on the
        basis of an invitation.
    """

    PUBLIC = "public"
    EXISTING = "existing"
    NOBODY = "nobody"

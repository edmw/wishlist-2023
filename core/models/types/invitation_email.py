class InvitationEmail(str):
    """Model field type for the email address of an invitation’s invitee.

    Specifies the maximum possible length of the email address.
    """

    max_length = 254

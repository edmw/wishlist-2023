class PushoverKey(str):
    """Model field type for a key to access Pushover.

    Specifies the minimum and maximum possible length of a key text.
    """

    max_length = 64

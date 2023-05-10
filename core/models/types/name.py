class Name(str):
    """Model field type for a wish’s or wishlist’s title.

    Specifies the minimum and maximum possible length of a title text.
    """

    min_length = 4
    max_length = 200

"""Mixin for models that want to provide a caption."""
from typing import Callable

from django.utils.text import Truncator


class Captionable:
    """Mixin for models that want to provide a caption.

    The model needs to provide a `captionable` callable which should return
    the text to create a preview for. To get a caption string clients just
    call `instance.caption()`.
    """

    captionable: Callable[[], str]

    def caption(self, number_of_chars: int = 25) -> str:
        """Returns a caption text for the model.

        Builds the caption text from the text string returned by the specified
        `captionable` callable.

        Arguments:
            number_of_chars: Caption is truncated to be no longer than the
                specified number of characters. Defaults to 25.

        Returns:
            The caption string.
        """
        return Truncator(self.captionable()).chars(number_of_chars, truncate=" …")

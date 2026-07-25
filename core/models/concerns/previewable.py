"""Mixin for models that want to provide a preview."""

from django.utils.text import Truncator


class Previewable:
    """Mixin for models that want to provide a preview.

    The model needs to provide a `previewable` callable which should return
    the text to create a preview for. To get a preview string clients just
    call `instance.preview()`.
    """

    def previewable(self) -> str:
        raise NotImplementedError("Subclasses must implement previewable()")

    def preview(self, number_of_words: int = 25) -> str:
        """Returns a preview text for the model.

        Builds the preview text from the text string returned by the specified
         `previewable` callable.

        Arguments:
            number_of_words: Preview is truncated to be no longer than the
                specified number of words. Defaults to 25.

        Returns:
            The preview string.
        """
        return Truncator(self.previewable()).words(number_of_words, truncate="…")

"""Image services."""

import logging

import requests
from PIL import Image

logger = logging.getLogger(__name__)


class ImageServiceError(Exception):
    ...


class ImageRetrieveTimeoutError(ImageServiceError):
    """Raised if the image could not be retrieved within the specified time
    period.
    """


class ImageService:
    """Image service: The image service provides functions for handling images."""

    @staticmethod
    def generate_jpeg_image_from_url(*, url: str) -> Image.Image:
        try:
            image = Image.open(requests.get(url, stream=True, timeout=2).raw)
            width, height = image.size
            offset = int(abs(height - width) / 2)
            if width > height:
                b = (offset, 0, width - offset, height)
            elif width < height:
                b = (0, offset, width, height - offset)
            else:
                b = (0, 0, width, height)
            return image.convert("RGB").resize((512, 512), box=b)
        except requests.exceptions.Timeout as timeout_error:
            raise ImageRetrieveTimeoutError() from timeout_error

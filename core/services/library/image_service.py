"""Image services."""

import logging

import requests
from PIL import Image, UnidentifiedImageError

logger = logging.getLogger(__name__)


class ImageServiceError(Exception): ...


class ImageServiceRetrieveTimeoutError(ImageServiceError):
    """Raised if the image could not be retrieved within the specified time period."""

    def __init__(self, url: str) -> None:
        super().__init__(f"Timeout while retrieving image from {url}")


class ImageServiceUnidentifiedImageError(ImageServiceError):
    """Raised if the image could not be identified."""

    def __init__(self, url: str) -> None:
        super().__init__(f"Unidentified image from {url}")


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
            raise ImageServiceRetrieveTimeoutError(url=url) from timeout_error
        except UnidentifiedImageError as unidentified_image_error:
            raise ImageServiceUnidentifiedImageError(url=url) from unidentified_image_error

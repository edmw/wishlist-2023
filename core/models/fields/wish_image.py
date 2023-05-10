from hashlib import sha256
from io import BytesIO
from typing import Any

from django.core.files import File
from django.db import models
from django.db.models.fields.files import ImageFieldFile
from PIL import Image


class WishImageFieldFile(ImageFieldFile):
    def update(self, name: str, image: Image.Image) -> None:
        image_name = sha256(name.encode("utf_32")).hexdigest()
        with BytesIO() as f:
            image.save(f, format="JPEG")
            self.save(f"{image_name}.jpg", File(f))


class WishImageField(models.ImageField):
    """Model field describing a wish’s image."""

    description = "Image of a Wish"
    attr_class = WishImageFieldFile

    def __init__(self, *args: Any, **kwargs: Any):
        """Initializes the field as image field."""
        kwargs["verbose_name"] = "Wish Image"
        kwargs["help_text"] = self.description
        kwargs["db_column"] = "image"
        kwargs["null"] = True
        kwargs["blank"] = True
        kwargs["max_length"] = 400
        kwargs["upload_to"] = "wishes"
        super().__init__(*args, **kwargs)

"""Create Password command."""

from typing import Any
from uuid import uuid4

from django.contrib.auth.hashers import make_password

from ._base import WebappBaseCommand


class Command(WebappBaseCommand):
    """Create Password command: Create password hash for random password string."""

    help = "Creates a password hash for a random password string."

    def handle(self, *args: Any, **options: Any) -> None:
        """Creates random password."""
        self.banner(["WEBAPP CREATE PASSWORD", self.help])

        random = str(uuid4())
        random_password = make_password(random)

        print(random_password)

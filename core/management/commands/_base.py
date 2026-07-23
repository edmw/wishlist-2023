from functools import partial, update_wrapper
from typing import Callable, TypeVar
from uuid import UUID

from core.models.types import UserID, WishID, WishlistID
from webapp.management.commands import WebappBaseCommand
from webapp.services import Base62Service

ID_TYPE = TypeVar("ID_TYPE", UserID, WishID, WishlistID)


class CoreBaseCommand(WebappBaseCommand):

    def id_from_string(self, id_string: str, id_type: type[ID_TYPE]) -> ID_TYPE:
        """Converts the specified string into an ID of the specified type.

        First, tries to convert the string to an UUID using Base62 encoding. If
        this fails, tries to convert the string to an UUID from a hex srtring.

        Then converts the UUID to the desired ID type.
        """
        try:
            uuid = Base62Service.uuid_decode(base62_string=id_string)
        except ValueError:
            uuid = UUID(hex=id_string)
        return id_type(bytes=uuid.bytes)

    def id_argument(self, id_type: type[ID_TYPE]) -> Callable[[str], ID_TYPE]:
        """Returns a callable which can be used for types of argparse.

        Creates a callable when called with a string will return an ID of type
        ID_TYPE:

        ```
        parser.add_argument(
            "--wish-id",
            type=self.id_argument(WishID),
            metavar="ID",
            help=(
                "ID of the wish."
            ),
        ```
        """
        return update_wrapper(partial(self.id_from_string, id_type=id_type), self.id_from_string)

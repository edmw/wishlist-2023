"""URL services."""

import logging
import re
from urllib.parse import parse_qs, urlencode, urlparse

logger = logging.getLogger(__name__)


class URLService:
    """URL service: The url service provides functions for handling urls."""

    RE_URL_ABSOLUTE_PATH = re.compile(r"^\/([^\/]|$)")

    @staticmethod
    def url_is_absolute_path(*, url: str) -> bool:
        """Checks if the given URL is a url without scheme and host and has an
        absolute path.

        Arguments:
            url: The URL to test.

        Returns:
            True, if URL is an absolute path, False otherwise.
        """
        return bool(URLService.RE_URL_ABSOLUTE_PATH.match(url))

    @staticmethod
    def update_query_parameters(
        *,
        url: str,
        parameters: dict[str, list[str]],
    ) -> str:
        """Updates the specified URL to include the specified query parameters.

        Preserves any query parameter already given at the URL. If any of the
        parameters given already exists for the URL, overwrites the existing
        value with the new value specified.

        Arguments:
            url: The URL to update.
            parameters: Dictionary with parameters to append to the URL.

        Returns:
            The URL with the parameters appended.
        """
        parsed_url = urlparse(url)
        url_query = parsed_url.query
        parsed_parameters = parse_qs(url_query)
        updated_parameters = {**parsed_parameters, **parameters}
        updated_url_query = urlencode(updated_parameters, doseq=True)
        url = parsed_url._replace(query=updated_url_query).geturl()
        return url

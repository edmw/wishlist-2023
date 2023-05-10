"""All about viewing the legal notice."""

import logging

from core.views._base import LocalizedTemplateView
from webapp.views.caching import AddNeverCacheMixin

logger = logging.getLogger(__name__)


class LegalNoticeView(AddNeverCacheMixin, LocalizedTemplateView):
    """The view for the legal notice."""

    http_method_names = ["get", "head", "options"]

    template_name = "legal_notice.html"

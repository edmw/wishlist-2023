"""All about viewing the privacy policy."""

import logging

from core.views._base import LocalizedTemplateView
from webapp.views.caching import AddNeverCacheMixin

logger = logging.getLogger(__name__)


class PrivacyPolicyView(AddNeverCacheMixin, LocalizedTemplateView):
    """The view for the privacy policy."""

    http_method_names = ["get", "head", "options"]

    template_name = "privacy_policy.html"

"""Urls defined by the Core Health application.

These url patterns are included in the root url patterns of the webapp.
"""

from django.urls import path

from core_health.views.healthcheck import healthcheck
from core_health.views.liveness import liveness
from core_health.views.readiness import readiness

urlpatterns = [
    path("health", healthcheck, name="healthcheck"),
    path("health/liveness", liveness, name="liveness"),
    path("health/readiness", readiness, name="readiness"),
]

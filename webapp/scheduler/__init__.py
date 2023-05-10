"""The webapp’s task scheduler."""

import os

from .healthcheck import healthcheck
from .scheduler import scheduler

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webapp.settings")

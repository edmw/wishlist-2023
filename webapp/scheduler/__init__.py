"""The webapp’s task scheduler."""

import os

# IMPORTANT: This default must be set before any other imports to ensure
# that the settings are loaded before the scheduler is initialized.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webapp.settings")

from .healthcheck import healthcheck
from .scheduler import scheduler

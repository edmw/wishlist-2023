#!/usr/bin/env python
"""Django command-line script."""
import os
import sys


def main() -> None:
    """Executes Django command given from command line arguments."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webapp.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as error:
        raise ImportError("Error importing Django") from error
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()

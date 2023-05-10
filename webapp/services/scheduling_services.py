"""Provides service functions for task scheduling."""

from datetime import datetime

from django.db.models import Count
from django_celery_results.models import TaskResult


class SchedulingService:
    """Service class providing a collection of static functions for task scheduling."""

    @staticmethod
    def count_task_results(*, since: datetime) -> dict[str, int]:
        """Counts the different states of all task results since the specified
        date.

        Returns a mapping from each found task status to the number of
        occurrences.
        """
        counters = (
            TaskResult.objects.values("status")
            .filter(date_done__gt=since)
            .annotate(total=Count("pk"))
            .order_by()
        )
        return {counter["status"]: counter["total"] for counter in counters}
